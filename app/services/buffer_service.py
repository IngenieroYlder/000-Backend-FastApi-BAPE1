import asyncio
import logging
from typing import Dict, List, Optional
from app.database import engine
from sqlmodel import Session, select
from datetime import datetime, timedelta
from app.models import CompanySettings, Message, MessageRole, MessageType, WhatsAppSession, Contact, Service
from app.services.ai_service import ai_service
from app.config import BAILEYS_ENGINE_URL
import httpx

logger = logging.getLogger(__name__)

class BufferService:
    def __init__(self):
        # Key: session_name_remote_jid -> { "task": asyncio.Task, "messages": [str], "data": dict }
        self.buffers: Dict[str, Dict] = {}
        self.timeout = 5.0 # Seconds to wait
        
    def _generate_date_reference(self) -> str:
        from datetime import datetime, timedelta
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        now = datetime.now()
        ref = "\n### [TABLA DE REFERENCIA DE FECHAS]\n"
        ref += "Usa esta tabla para no calcular fechas mentalmente:\n"
        for i in range(8):
            dt = now + timedelta(days=i)
            day_name = "HOY" if i == 0 else "MAÑANA" if i == 1 else dias[dt.weekday()].upper()
            ref += f"- {day_name}: {dt.strftime('%Y-%m-%d')}\n"
        return ref

    # Class-level tracker for provider health (persist across class life in this process)
    # Key: (company_id, provider), Value: expiry_datetime
    _provider_cooldowns: Dict[tuple, datetime] = {}

    def _is_provider_healthy(self, company_id: int, provider: str) -> bool:
        key = (company_id, provider)
        if key in self._provider_cooldowns:
            if datetime.now() < self._provider_cooldowns[key]:
                return False
            else:
                del self._provider_cooldowns[key]
        return True

    def _set_provider_cooldown(self, company_id: int, provider: str, minutes: int = 5):
        self._provider_cooldowns[(company_id, provider)] = datetime.now() + timedelta(minutes=minutes)
        print(f"[Buffer AI] Cooldown SET for {provider} (Company {company_id}) for {minutes}m")

    async def add_message(self, session_name: str, remote_jid: str, text: str, data: dict, message_key: dict = None):
        key = f"{session_name}_{remote_jid}"
        
        # 1. Mark as Read immediately
        if message_key:
            asyncio.create_task(self._mark_read(session_name, remote_jid, message_key))

        if key not in self.buffers:
            self.buffers[key] = {
                "task": None,
                "messages": [],
                "data": data # Context data (company_id, contact_id, etc.)
            }
        
        # Add message to buffer
        self.buffers[key]["messages"].append(text)
        
        # Cancel previous timer if exists
        if self.buffers[key]["task"]:
            self.buffers[key]["task"].cancel()
            
        # Start new timer
        self.buffers[key]["task"] = asyncio.create_task(self._process_buffer(key, session_name, remote_jid))
        print(f"[Buffer] Message buffered for {key}. Timer restarted ({self.timeout}s). Pending: {len(self.buffers[key]['messages'])}")

    async def _process_buffer(self, key: str, session_name: str, remote_jid: str):
        try:
            # Send 'composing' logic could be here if we want to simulate typing DURING the buffer wait? 
            # Or better, wait until buffer expires -> THEN type -> THEN send.
            # Let's wait first.
            await asyncio.sleep(self.timeout)
            
            # Timer expired, process messages
            buffer_data = self.buffers.pop(key, None)
            if not buffer_data:
                return

            messages = buffer_data["messages"]
            data = buffer_data["data"]
            
            combined_text = "\n".join(messages)
            print(f"[Buffer] Processing {len(messages)} messages for {key}. Combined text: {combined_text[:50]}...")
            
            # Start Typing Indicator
            await self._set_presence(session_name, remote_jid, "composing")
            
            await self._generate_and_send_response(combined_text, data, key)

            # Stop Typing (optional, usually message sending stops it, but good practice)
            await self._set_presence(session_name, remote_jid, "paused")
            
        except asyncio.CancelledError:
            # Task was cancelled, meaning a new message arrived or buffer was cleared externally
            pass
        except Exception as e:
            logger.error(f"Error processing buffer for {key}: {e}")
            import traceback
            traceback.print_exc()

    async def _mark_read(self, session_name: str, jid: str, message_key: dict):
        try:
             async with httpx.AsyncClient() as client:
                await client.post(f"{BAILEYS_ENGINE_URL}/message/read", json={
                    "session_name": session_name,
                    "jid": jid,
                    "message_key": message_key
                })
        except Exception as e:
            print(f"[Buffer] Error marking read: {e}")

    async def _set_presence(self, session_name: str, jid: str, state: str):
        try:
             async with httpx.AsyncClient() as client:
                await client.post(f"{BAILEYS_ENGINE_URL}/session/presence", json={
                    "session_name": session_name,
                    "jid": jid,
                    "presence": state
                })
        except Exception as e:
             print(f"[Buffer] Error setting presence {state}: {e}")

    async def _generate_and_send_response(self, text_content: str, data: dict, key: str):
        # We need a new session because we are in a background task
        with Session(engine) as session:
            try:
                company_id = data["company_id"]
                contact_id = data["contact_id"]
                wa_session_id = data["wa_session_id"]
                # wa_alias = data["wa_alias"]
                session_name = key.split("_", 2)[0] + "_" + key.split("_", 2)[1] # Hacky default, better use data["session_name"]
                # Actually, key is session_name_remote_jid. 
                # Let's trust data passed.
                session_name = data["session_name"]
                remote_jid = data["remote_jid"]
                
                # Fetch settings again to be fresh
                # Fetch Contact to get summary
                contact = session.get(Contact, contact_id)
                
                # Fetch settings again to be fresh
                stmt_settings = select(CompanySettings).where(CompanySettings.company_id == company_id)
                company_settings = session.exec(stmt_settings).first()

                stmt_session = select(WhatsAppSession).where(WhatsAppSession.id == wa_session_id)
                wa_session = session.exec(stmt_session).first()
                
                if not wa_session:
                    print(f"[Buffer] Session {wa_session_id} not found.")
                    return

                global_prompt = company_settings.system_prompt if company_settings else None
                # Base instruction is just the system prompt for now
                base_instruction = wa_session.system_prompt or global_prompt or "Eres un asistente de atención al cliente amable y profesional."
                
                # INJECT GOLDEN RULES
                if company_settings and company_settings.golden_rules:
                    base_instruction += f"\n\n### REGLAS DE ORO:\n{company_settings.golden_rules}"
                
                # FETCH SERVICES
                stmt_services = select(Service).where(Service.company_id == company_id)
                services = session.exec(stmt_services).all()
                if services:
                    services_list = "\n".join([f"- {s.name}: {s.description or ''}" for s in services])
                    base_instruction += f"\n\n### TIPOS DE CITA / SERVICIOS DISPONIBLES:\n{services_list}\n(Ofrece estas opciones al usuario para su cita)"
                
                # INJECT KNOWLEDGE BASE (RAG)
                from app.services.rag_service import rag_service
                
                # Check if we have processed documents first (optimization to avoid embedding if no docs exist)
                # actually retrieve_context handles empty results gracefully
                
                kb_context = await rag_service.retrieve_context(text_content, company_id)
                if kb_context:
                    base_instruction += kb_context

                # INJECT SUMMARY IF EXISTS
                if contact and contact.summary:
                    base_instruction += f"\n\n### RESUMEN DE CONVERSACIÓN PREVIA:\n{contact.summary}\n(Usa este contexto para no preguntar lo mismo)"

                # FETCH RECENT HISTORY (Short-Term Memory)
                # Essential for multi-turn flows like booking where date/time was mentioned in previous turn.
                recent_msgs = session.exec(
                    select(Message)
                    .where(Message.contact_id == contact_id)
                    .order_by(Message.created_at.desc())
                    .limit(20) # Increased to 20 for robust context (handles short "Yes" replies correctly)
                ).all()
                recent_msgs.reverse() # Oldest first
                
                history_context = ""
                for m in recent_msgs:
                    role_label = "AI" if m.role == MessageRole.ASSISTANT else "User"
                    # Avoid duplicating the current message if it was somehow already saved (unlikely here as we save after)
                    if m.content:
                        history_context += f"{role_label}: {m.content}\n"
                
                # Append current user message (text_content) effectively handled in loop, 
                # but we need to initialize conversation_history with context.
                # Actually, ai_service.generate_response expects the 'prompt'.
                # We should construct: History + "\nUser: " + Current Input
                
                # However, our ai_service might treat the whole string as the user prompt if we aren't careful.
                # Ideally we pass formatted history. For now, let's prepend to text_content.
                
                conversation_history = f"{history_context}User: {text_content}"

                # Logic: Provider Selection & Fallback
                strategy = wa_session.ai_strategy or "fixed"
                preferred_provider = wa_session.ai_provider or "openai"
                
                # 1. Build list of ALL configured providers
                all_providers = []
                if company_settings:
                    if company_settings.openai_api_key: all_providers.append(("openai", company_settings.openai_api_key))
                    if company_settings.groq_api_key: all_providers.append(("groq", company_settings.groq_api_key))
                    if company_settings.gemini_api_key: all_providers.append(("gemini", company_settings.gemini_api_key))

                # 2. Filter by health (skip known limits/errors)
                available_providers = [p for p in all_providers if self._is_provider_healthy(company_id, p[0])]
                
                if not available_providers and all_providers:
                    print(f"[Buffer AI] All configured providers ({[p[0] for p in all_providers]}) are in cooldown. Trying them anyway as last resort (filtered out {len(all_providers) - len(available_providers)}).")
                    available_providers = all_providers # Emergency fallback: try anyway

                # 3. Sort based on strategy
                if strategy == "rotate_free":
                    # Free Tier Priority: Groq/Gemini first, OpenAI last
                    def free_priority_sort(p):
                        prov_name = p[0]
                        # First priority: Free ones
                        if prov_name in ["groq", "gemini"]:
                            # If it is the preferred one, even better
                            return 0 if prov_name == preferred_provider else 1
                        # Second priority: Paid ones
                        return 2
                    available_providers.sort(key=free_priority_sort)
                else:
                    # Fixed strategy or default: Respect preferred provider
                    if preferred_provider:
                        available_providers.sort(key=lambda x: 0 if x[0] == preferred_provider else 1)

                if not available_providers:
                    print("[Buffer AI] No providers configured.")
                    return

                # Call AI with Tool Use Loop
                max_turns = 3
                current_turn = 0
                final_response = ""
                
                # Context for Calendar
                from app.models import AppointmentConfig
                stmt_cal = select(AppointmentConfig).where(AppointmentConfig.company_id == company_id)
                cal_config = session.exec(stmt_cal).first()
                if cal_config and cal_config.google_access_token:
                    from datetime import datetime
                    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                    ahora = datetime.now()
                    nombre_dia = dias_semana[ahora.weekday()]
                    now_str = ahora.strftime("%Y-%m-%d %H:%M")
                    base_instruction += f"\n\n[SISTEMA: HOY ES {nombre_dia.upper()}, {now_str}]"
                    base_instruction += (
                        "\n\n### [MANEJO DE AGENDA Y DISPONIBILIDAD]"
                        "\n- Si el usuario pregunta por disponibilidad o quiere agendar, TU PRIMERA ACCIÓN debe ser generar un comando."
                        "\n- COMANDOS PERMITIDOS:"
                        "\n  * CHECK_AVAILABILITY date='YYYY-MM-DD'"
                        "\n  * BOOK_SLOT date='YYYY-MM-DD' time='HH:MM' email='user@email.com' name='Nombre' description='Motivo/Tipo de Servicio'"
                        "\n- REQUISITOS PARA BOOK_SLOT:"
                        "\n  1. Debes tener la FECHA y HORA confirmadas (puedes usar CHECK_AVAILABILITY primero)."
                        "\n  2. DEBES solicitar y tener el NOMBRE COMPLETO, CORREO ELECTRÓNICO y el MOTIVO/SERVICIO antes de generar BOOK_SLOT."
                        "\n  3. Si faltan datos, NO generes BOOK_SLOT; pídelos amablemente primero."
                        "\n- IMPORTANTE: Si vas a usar un comando, RESPONDE SOLO EL COMANDO en ese turno. En el siguiente turno, cuando el sistema te dé los datos, responde con calidez humana."
                        "\n- FECHAS: Calcula 'mañana' sumando 1 día a la fecha actual. Si hoy es Viernes, mañana es Sábado. NUNCA uses la fecha de HOY para una solicitud de MAÑANA."
                        "\n  * Si el usuario menciona un día de la semana (ej: Sábado), asegúrate de que la fecha coincida con ese día."
                        "\n- NO INVENTES: Si el sistema devuelve 'Ninguno', dile al usuario de forma amable que ese día no hay servicio o está lleno."
                        "\n- RESPUESTA FINAL: Menciona siempre el día y fecha exacta en tu respuesta final: 'Para el sábado 21 de febrero tenemos...'"
                    )
                
                # conversation_history is already initialized with history + current message above
                from app.services.ai_service import AIRateLimitError

                while current_turn < max_turns:
                    # Pick provider
                    if not available_providers: break
                    current_provider, current_key = available_providers[0]

                    # ---------------------------------------------------------
                    # DYNAMIC SYSTEM INSTRUCTION PER TURN
                    # ---------------------------------------------------------
                    active_instruction = base_instruction
                    
                    if current_turn == 0:
                        # Turn 0: If AI decides to use commands, it must NOT chat alongside them.
                        active_instruction = (
                            base_instruction + 
                            "\n\n### [REGLA CRÍTICA DE USO DE HERRAMIENTAS]" +
                            "\nSi decides que es necesario usar CHECK_AVAILABILITY o BOOK_SLOT, RESPONDE ÚNICAMENTE con el comando en este turno." +
                            "\nESTÁ PROHIBIDO añadir texto conversacional en el mismo turno que un comando."
                        )
                    else:
                        # Turn 1+: Personality and Human Response (after tools)
                        active_instruction += (
                            "\n\n### REGLAS DE RESPUESTA FINAL:"
                            "\n1. Habla de forma natural, humana y profesional basándote en los datos del sistema."
                            "\n2. Si recibiste un [SISTEMA: Espacios disponibles...], infórmalo clara y amablemente."
                        )


                    print(f"[Buffer AI] Generating response (Turn {current_turn}) with {current_provider}...")
                    try:
                        ai_response = await ai_service.generate_response(conversation_history, active_instruction, current_provider, current_key)
                    except AIRateLimitError:
                        if strategy == "rotate_free" and len(available_providers) > 1:
                            print(f"[Buffer AI] {current_provider} rate limited. Rotating...")
                            
                            # LOG EVENT
                            self._save_log(session, company_id, "rotation", current_provider, f"Límite alcanzado. Rotando a {available_providers[1][0]}")
                            
                            # SET COOLDOWN
                            self._set_provider_cooldown(company_id, current_provider, minutes=10) # 10m for Rate Limits
                            
                            available_providers.pop(0) # Remove failed provider
                            continue # Try next one
                        else:
                            ai_response = f"Error: Límite de cuota alcanzado en {current_provider}."
                            self._save_log(session, company_id, "error", current_provider, "Límite de cuota alcanzado. Sin más proveedores disponibles.")
                    except Exception as e:
                        print(f"[Buffer AI] Unexpected error with {current_provider}: {e}")
                        if strategy == "rotate_free" and len(available_providers) > 1:
                            print(f"[Buffer AI] Technical error with {current_provider}. Rotating...")
                            self._save_log(session, company_id, "rotation", current_provider, f"Error técnico ({str(e)}). Rotando a {available_providers[1][0]}")
                            
                            # SET COOLDOWN
                            self._set_provider_cooldown(company_id, current_provider, minutes=5) # 5m for technical errors
                            
                            available_providers.pop(0)
                            continue
                        else:
                            ai_response = f"Error técnico con {current_provider}."
                            self._save_log(session, company_id, "error", current_provider, f"Error inesperado: {str(e)}")
                    
                    # If we got an error string (like 401) and have rotation enabled, rotate!
                    if (ai_response.startswith("Error:") or ai_response.startswith("Error técnico")) and strategy == "rotate_free" and len(available_providers) > 1:
                        print(f"[Buffer AI] {current_provider} returned an error. Rotating...")
                        self._save_log(session, company_id, "rotation", current_provider, f"Error detectado: {ai_response}. Rotando...")
                        
                        # SET COOLDOWN
                        self._set_provider_cooldown(company_id, current_provider, minutes=5)
                        
                        available_providers.pop(0)
                        continue

                    # Tool Use Detection
                    if "CHECK_AVAILABILITY" in ai_response:
                        try:
                            # Extract Params
                            # Expected: CHECK_AVAILABILITY date='2023-10-27' time='14:00' (optional)
                            import re
                            date_match = re.search(r"date='([^']+)'", ai_response)
                            time_match = re.search(r"time='([^']+)'", ai_response)
                            
                            if date_match:
                                target_date = date_match.group(1)
                                target_time = time_match.group(1) if time_match else None
                                
                                from app.services.calendar_service import calendar_service
                                slots = calendar_service.get_available_slots(cal_config.id, target_date)
                                
                                formatted_slots = []
                                slot_times = set() # For quick lookup
                                for slot in slots:
                                    # Convert 2026-02-19T09:00:00-05:00 to 09:00 AM
                                    dt = datetime.fromisoformat(slot)
                                    fmt = dt.strftime("%I:%M %p")
                                    formatted_slots.append(fmt)
                                    slot_times.add(fmt)
                                    # Also add 24h format for easier matching
                                    slot_times.add(dt.strftime("%H:%M"))
                                
                                slots_str = ", ".join(formatted_slots) if formatted_slots else "Ninguno"
                                tool_output = f"\n[SISTEMA: Espacios disponibles para {target_date}: {slots_str}.]"

                                # Safeguard: Today vs Tomorrow mismatch
                                is_today = target_date == datetime.now().strftime("%Y-%m-%d")
                                if is_today and "mañana" in text_content.lower():
                                    tool_output += "\n[ADVERTENCIA SISTEMA: Has consultado fecha de HOY, pero el usuario dijo MAÑANA. Por favor, rectifica la fecha de mañana (+1 día) en tu respuesta o consulta de nuevo.]"
                                
                                if not formatted_slots:
                                    tool_output += "\n[SISTEMA: Confirmado, no hay ningún espacio disponible para esta fecha. Explica al usuario de forma muy amable que el día está cerrado o sin cupos y sugiérele buscar otra fecha.]"
                                
                                # Only verify if the AI explicitly provided a time AND it's not simply the current time
                                now_time = datetime.now().strftime("%H:%M")
                                if target_time and target_time != now_time:
                                    # Normalize target_time to match our set
                                    try:
                                        t_dt = datetime.strptime(target_time, "%H:%M")
                                        t_fmt_12 = t_dt.strftime("%I:%M %p")
                                        t_fmt_24 = t_dt.strftime("%H:%M")
                                        
                                        if t_fmt_12 in slot_times or t_fmt_24 in slot_times:
                                            tool_output += f"\n[VERIFICACIÓN: La hora {target_time} SÍ está disponible. ¡Ofrécela!]"
                                        else:
                                            # If not available, we should ONLY say it's not available if slots were found for the day.
                                            # If no slots were found at all, the previous CRÍTICO message covers it.
                                            if formatted_slots:
                                                tool_output += f"\n[VERIFICACIÓN: La hora {target_time} NO está disponible (Está OCUPADA o fuera de horario). Ofrece los horarios libres listados arriba.]"
                                    except:
                                        pass
                                else:
                                    if formatted_slots:
                                        tool_output += f"\n[INSTRUCCIÓN: Informa al usuario sobre los espacios libres listados arriba de forma amable para que elija el que más le convenga.]"
                                
                                print(f"[Tool Output] {tool_output}")
                                
                                # Append to history and loop
                                conversation_history += f"\nAI: {ai_response}\nSYSTEM: {tool_output}\n(Ahora responde al usuario)"
                                current_turn += 1
                                continue
                        except Exception as e:
                            print(f"[Tool Error] {e}")

                    elif "BOOK_SLOT" in ai_response:
                        try:
                            # Expected: BOOK_SLOT date='...' time='...' email='...' name='...'
                            import re
                            date_m = re.search(r"date='([^']+)'", ai_response)
                            time_m = re.search(r"time='([^']+)'", ai_response)
                            email_m = re.search(r"email='([^']+)'", ai_response)
                            name_m = re.search(r"name='([^']+)'", ai_response) # Optional
                            desc_m = re.search(r"description='([^']+)'", ai_response)
                            address_m = re.search(r"address='([^']+)'", ai_response)
                            company_m = re.search(r"company='([^']+)'", ai_response)
                            job_m = re.search(r"job='([^']+)'", ai_response)
                            doc_id_m = re.search(r"doc_id='([^']+)'", ai_response)
                            
                            if date_m and time_m and email_m:
                                # Update Contact Professional Details
                                if contact:
                                    if not contact.email: contact.email = email_m.group(1)
                                    if address_m: contact.address = address_m.group(1)
                                    if company_m: contact.company_name = company_m.group(1)
                                    if job_m: contact.job_title = job_m.group(1)
                                    if doc_id_m: contact.document_id = doc_id_m.group(1)
                                    session.add(contact)
                                    session.commit()
                                target_date = date_m.group(1)
                                target_time = time_m.group(1)
                                email = email_m.group(1)
                                name = name_m.group(1) if name_m else "Cliente WhatsApp"
                                desc = desc_m.group(1) if desc_m else "Cita desde WhatsApp"
                                
                                # Parse datetime
                                start_dt = datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M")
                                end_dt = start_dt + timedelta(minutes=cal_config.slot_duration)
                                print(f'[Buffer] Creating appointment with duration: {cal_config.slot_duration} min (End: {end_dt})')
                                
                                from app.services.calendar_service import calendar_service
                                from app.models import Appointment

                                # --- CLEANUP DUPLICATES ---
                                stmt_old = select(Appointment).where(Appointment.company_id == company_id, Appointment.client_email == email, Appointment.status == 'confirmed')
                                existing_appts = session.exec(stmt_old).all()
                                for old_appt in existing_appts:
                                    if old_appt.google_event_id:
                                        calendar_service.delete_event(cal_config, old_appt.google_event_id)
                                    old_appt.status = 'cancelled'
                                    session.add(old_appt)
                                event = calendar_service.create_event(cal_config, start_dt, end_dt, f"Cita: {name}", desc, email)
                                
                                if event:
                                    # SAVE TO DB
                                    new_local_appt = Appointment(
                                        contact_id=contact.id if contact else None,
                                        company_id=company_id,
                                        title=f'Cita: {name}',
                                        start_time=start_dt,
                                        end_time=end_dt,
                                        client_name=name,
                                        client_phone=contact.phone if contact else 'Desconocido',
                                        client_email=email,
                                        google_event_id=event.get('id'),
                                        status='confirmed'
                                    )
                                    session.add(new_local_appt)
                                    session.commit()
                                    tool_output = f"\n[SISTEMA: Cita agendada con éxito. ID: {event.get('id')}]"
                                    
                                    # Send Email Confirmation
                                    try:
                                        from app.services.email_service import email_service
                                        email_body = (
                                            f"Hola {name},<br><br>"
                                            f"Su cita ha sido confirmada para el <b>{target_date} a las {target_time}</b>.<br>"
                                            f"Motivo: {desc}<br><br>"
                                            f"Gracias,<br>Equipo Agente IA"
                                        )
                                        email_service.send_email(email, "Confirmación de Cita", email_body)
                                    except Exception as e:
                                        print(f"[Email Error] Failed to send confirmation: {e}")

                                    # We can stop here or let AI confirm
                                    conversation_history += f"\nAI: {ai_response}\nSYSTEM: {tool_output}\n(Confirma al usuario que su cita quedó agendada)"
                                    current_turn += 1
                                    continue
                                else:
                                    tool_output = "\n[SISTEMA: Error al crear cita en Google Calendar.]"
                                    conversation_history += f"\nAI: {ai_response}\nSYSTEM: {tool_output}"
                                    current_turn += 1
                                    continue
                        except Exception as e:
                            print(f"[Tool Error] {e}")
                    
                    # If no tool triggered or loop finished, use this as final response
                    final_response = ai_response
                    break
                
                print(f"[Buffer AI] Final Response: {final_response}")
                
                # FALLBACK FOR TECHNICAL ERRORS
                if final_response.lower().startswith("error") or "error técnico" in final_response.lower():
                    logger.warning(f"[Buffer AI] Technical error detected. Sending fallback to user: {final_response}")
                    final_response = "Lo siento, estamos experimentando una alta demanda o un problema técnico temporal. Por favor, intenta de nuevo en unos minutos."
                
                # LOG SUCCESSFUL ACTION
                self._save_log(session, company_id, "info", current_provider, f"🤖 Respondiendo a: '{text_content[:30]}...' -> {final_response[:50]}...")

                # Save Bot Message
                bot_msg = Message(
                    company_id=company_id,
                    contact_id=contact_id,
                    session_id=wa_session_id,
                    role=MessageRole.ASSISTANT,
                    content=final_response,
                    type=MessageType.TEXT
                )
                session.add(bot_msg)
                session.commit()
                
                # Send via Baileys
                async with httpx.AsyncClient() as client:
                    payload = {
                        "session_name": session_name,
                        "jid": remote_jid,
                        "message": {"text": final_response}
                    }
                    await client.post(f"{BAILEYS_ENGINE_URL}/message/send", json=payload)
                
                # Trigger Summary Update (Fire and Forget)
                asyncio.create_task(self._update_summary_if_needed(contact_id, company_id, current_provider, current_key))

            except Exception as e:
                logger.error(f"Error in async AI generation: {e}")
                print(f"[Buffer Error] {e}")

    async def _update_summary_if_needed(self, contact_id: int, company_id: int, provider: str, api_key: str):
        """
        Check if conversation is long enough to require a summary update.
        """
        try:
            with Session(engine) as session:
                from app.models import CompanySettings
                c_settings = session.exec(select(CompanySettings).where(CompanySettings.company_id == company_id)).first()
                sys_prompt = c_settings.summary_prompt if c_settings else None

                # Count messages
                # Simple heuristic: If count > 20, we summarize.
                # Or we can just summarize every 10 messages from the last summary date?
                # For now, let's just fetch all recent messages and see.
                
                # Actually, counting is fast.
                from sqlalchemy import func
                count = session.exec(select(func.count(Message.id)).where(Message.contact_id == contact_id)).one()
                
                if count >= 10: # Lower limit for testing, usually 20-50
                    print(f"[Summary] Contact {contact_id} has {count} messages. Updating summary...")
                    
                    # Fetch last 50 messages to form the context
                    msgs = session.exec(select(Message).where(Message.contact_id == contact_id).order_by(Message.created_at.desc()).limit(50)).all()
                    msgs.reverse() # Chronological order
                    
                    # Filter out technical errors from history to avoid corrupting the summary
                    history_text = "\n".join([
                        f"{m.role}: {m.content}" 
                        for m in msgs 
                        if m.content and not (m.content.lower().startswith("error") or "límite" in m.content.lower() or "probema técnico" in m.content.lower())
                    ])
                    
                    # Generate Summary
                    new_summary = await ai_service.summarize_conversation(history_text, provider, api_key, sys_prompt)
                    
                    # BLOCK SYMBOLIC ERRORS FROM SAVING
                    if not new_summary or new_summary.lower().startswith("error"):
                        print(f"[Summary] AI returned error for summary. Skipping update.")
                        return

                    # Update Contact
                    contact = session.get(Contact, contact_id)
                    contact.summary = new_summary
                    contact.last_chat_date = datetime.now()
                    session.add(contact)
                    
                    # Optional: Delete old messages here if policy allows.
                    # For now, we keep them.
                    
                    session.commit()
                    print(f"[Summary] Updated summary for Contact {contact_id}: {new_summary[:50]}...")
                    
        except Exception as e:
            print(f"[Summary Error] {e}")

    def _save_log(self, session: Session, company_id: int, event_type: str, provider: str, message: str, details: dict = {}):
        try:
            from app.models import SystemLog
            new_log = SystemLog(
                company_id=company_id,
                event_type=event_type,
                provider=provider,
                message=message,
                details=details
            )
            session.add(new_log)
            session.commit()
        except Exception as e:
            print(f"[Log Error] Failed to save system log: {e}")

buffer_service = BufferService()
