import logging
import json

logger = logging.getLogger(__name__)

class QRCache:
    def __init__(self):
        self.cache = {} # session_name -> {"qr": str, "status": str, "metadata": dict}

    def set_qr(self, session_name: str, qr: str):
        data = self.cache.get(session_name.lower(), {"qr": None, "status": "initializing", "metadata": {}})
        data["qr"] = qr
        data["status"] = "qr_ready"
        self.cache[session_name.lower()] = data
        logger.info(f"[QR Cache] Set QR for {session_name}")

    def set_status(self, session_name: str, status: str):
        data = self.cache.get(session_name.lower(), {"qr": None, "status": "initializing", "metadata": {}})
        data["qr"] = None if status.lower() == "connected" else data.get("qr")
        data["status"] = status.lower()
        self.cache[session_name.lower()] = data
        logger.info(f"[QR Cache] Set status {status} for {session_name}")

    def update_metadata(self, session_name: str, metadata: dict):
        data = self.cache.get(session_name.lower(), {"qr": None, "status": "initializing", "metadata": {}})
        data["metadata"].update(metadata)
        # Also sync status if in metadata
        if "status" in metadata:
             data["status"] = metadata["status"].lower()
        self.cache[session_name.lower()] = data

    def get(self, session_name: str):
        return self.cache.get(session_name.lower())

    def get_by_id(self, session_id: int):
        for name, data in self.cache.items():
            if data["metadata"].get("id") == session_id:
                return name, data
        return None, None

    def get_all_for_company(self, company_id: int):
        results = []
        for name, data in self.cache.items():
            if data["metadata"].get("company_id") == company_id:
                # Reconstruct a dict that looks like WhatsAppSession
                s = {
                    "id": data["metadata"].get("id"),
                    "session_name": name,
                    "alias": data["metadata"].get("alias"),
                    "status": data["status"],
                    "qr_code": data["qr"],
                    "ai_provider": data["metadata"].get("ai_provider"),
                    "ai_strategy": data["metadata"].get("ai_strategy"),
                    "is_bot_enabled": data["metadata"].get("is_bot_enabled", True),
                    "respond_to_groups": data["metadata"].get("respond_to_groups", False),
                    "company_id": company_id
                }
                results.append(s)
        return results

qr_cache = QRCache()
