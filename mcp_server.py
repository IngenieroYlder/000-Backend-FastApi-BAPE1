import os
import asyncio
from typing import Any, List, Optional
from mcp.server.fastmcp import FastMCP
from sqlmodel import Session, select
from app.database import engine
from app import models

# Inicializar FastMCP
mcp = FastMCP("BAPE")

# --- RECURSOS ---

@mcp.resource("bape://catalog/products")
def get_products() -> str:
    """Retorna la lista de productos disponibles en el catálogo."""
    with Session(engine) as session:
        statement = select(models.Product)
        products = session.exec(statement).all()
        if not products:
            return "No hay productos registrados en el catálogo."
        
        output = "# Catálogo de Productos BAPE\n\n"
        for p in products:
            output += f"- **{p.name}**: ${p.price} (Stock: {p.stock})\n"
            if p.description:
                output += f"  _{p.description}_\n"
        return output

@mcp.resource("bape://catalog/services")
def get_services() -> str:
    """Retorna la lista de servicios disponibles en el catálogo."""
    with Session(engine) as session:
        statement = select(models.Service)
        services = session.exec(statement).all()
        if not services:
            return "No hay servicios registrados."
        
        output = "# Catálogo de Servicios BAPE\n\n"
        for s in services:
            output += f"- **{s.name}**: ${s.price}\n"
            if s.description:
                output += f"  _{s.description}_\n"
        return output

# --- HERRAMIENTAS (TOOLS) ---

@mcp.tool()
async def search_contacts(query: str) -> str:
    """
    Busca contactos en la base de datos por nombre o teléfono.
    """
    with Session(engine) as session:
        statement = select(models.Contact).where(
            (models.Contact.name.contains(query)) | 
            (models.Contact.phone.contains(query))
        )
        contacts = session.exec(statement).all()
        
        if not contacts:
            return f"No se encontraron contactos que coincidan con '{query}'."
        
        res = f"Resultados para '{query}':\n"
        for c in contacts:
            res += f"- ID: {c.id} | {c.name} ({c.phone})\n"
        return res

@mcp.tool()
async def get_recent_messages(contact_id: int, limit: int = 5) -> str:
    """
    Obtiene los últimos mensajes de un contacto específico.
    """
    with Session(engine) as session:
        statement = select(models.Message).where(
            models.Message.contact_id == contact_id
        ).order_by(models.Message.created_at.desc()).limit(limit)
        
        messages = session.exec(statement).all()
        if not messages:
            return "No hay mensajes registrados para este contacto."
        
        res = f"Últimos {len(messages)} mensajes:\n"
        for m in reversed(messages):
            sender = "Cliente" if m.sender_type == "customer" else "Bot/Agente"
            res += f"[{m.created_at.strftime('%Y-%m-%d %H:%M')}] {sender}: {m.text}\n"
        return res

@mcp.tool()
async def list_appointments(date: Optional[str] = None) -> str:
    """
    Lista las citas programadas. Si se provee una fecha (YYYY-MM-DD), filtra por ese día.
    """
    with Session(engine) as session:
        statement = select(models.Appointment)
        if date:
            # Filtrar por fecha de inicio (asumiendo que start_time es datetime)
            # Nota: Esto es simplificado para el ejemplo
            statement = statement.where(models.Appointment.start_time >= date)
        
        appointments = session.exec(statement).all()
        if not appointments:
            return "No hay citas programadas para el periodo seleccionado."
        
        res = "Citas programadas:\n"
        for a in appointments:
            status = "Confirmada" if a.is_confirmed else "Pendiente"
            res += f"- ID: {a.id} | {a.start_time} | Contacto ID: {a.contact_id} | Estado: {status}\n"
        return res

@mcp.tool()
async def create_appointment_manual(contact_id: int, start_time: str, description: str = "") -> str:
    """
    Crea una cita manual en la base de datos. 
    start_time debe estar en formato ISO (YYYY-MM-DD HH:MM:SS).
    """
    try:
        with Session(engine) as session:
            new_appo = models.Appointment(
                contact_id=contact_id,
                start_time=start_time,
                description=description,
                is_confirmed=True # Por ser manual
            )
            session.add(new_appo)
            session.commit()
            return f"Cita creada con éxito para el contacto {contact_id} en {start_time}."
    except Exception as e:
        return f"Error al crear la cita: {str(e)}"

if __name__ == "__main__":
    # El servidor MCP se comunica via stdio por defecto
    mcp.run()
