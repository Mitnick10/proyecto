import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

# Configurar logger local para este módulo
logger = logging.getLogger(__name__)

load_dotenv()

class SupabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._client = None
        self._admin = None
        
        self.url = os.environ.get('SUPABASE_URL')
        self.key = os.environ.get('SUPABASE_KEY')
        self.service_key = os.environ.get('SUPABASE_SERVICE_KEY')
        
        self._initialize_clients()
        self._initialized = True
    
    def _initialize_clients(self):
        try:
            if not self.url or not self.key:
                raise ValueError("SUPABASE_URL y SUPABASE_KEY son requeridas en .env")
                
            # 1. Cliente Standard (Anon Key)
            self._client = create_client(self.url, self.key)
            logger.info("✅ Cliente Supabase (Anon) inicializado.")
            
            # 2. Cliente Admin (Service Role Key)
            if self.service_key:
                self._admin = create_client(self.url, self.service_key)
                logger.info("✅ Cliente Supabase Admin (Service Role) inicializado.")
            else:
                logger.warning("⚠️ Cliente Supabase Admin NO inicializado (Falta Service Key).")
                
        except Exception as e:
            logger.critical(f"❌ Error fatal inicializando SupabaseManager: {e}")
            # No relanzamos para no crashear la app entera al importar, 
            # pero los clientes quedarán como None
            
    @property
    def client(self):
        if self._client is None:
            logger.error("Intento de acceso a supabase.client fallido (no inicializado).")
            # Podríamos intentar reinicializar aquí si fuera deseable
        return self._client
        
    @property
    def admin(self):
        if self._admin is None:
            logger.error("Intento de acceso a supabase.admin fallido (no configurado o inicializado).")
        return self._admin

# Instancia Singleton Global
_manager = SupabaseManager()

# Exportar instancias para mantener compatibilidad con imports existentes
supabase = _manager.client
supabase_admin = _manager.admin