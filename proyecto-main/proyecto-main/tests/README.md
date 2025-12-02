# 🧪 Tests Unitarios - Guía Completa

## 📋 ¿Qué son los Tests Unitarios?

Los tests unitarios son programas pequeños que verifican que cada "unidad" (función/método) de tu código funciona correctamente de forma aislada.

### Ejemplo Simple
```python
# Tu función
def sumar(a, b):
    return a + b

# Tu test
def test_sumar():
    resultado = sumar(2, 3)
    assert resultado == 5  # ✅ Si pasa, el test aprueba
```

---

## 🚀 Instalación

### 1. Instalar pytest
```bash
pip install pytest pytest-cov
```

### 2. Agregar al requirements.txt
```
pytest==7.4.3
pytest-cov==4.1.0
```

---

## ▶️ Cómo Ejecutar los Tests

### Ejecutar todos los tests
```bash
pytest
```

### Ejecutar con más detalles (verbose)
```bash
pytest -v
```

### Ejecutar solo un archivo de tests
```bash
pytest tests/test_validaciones.py
```

### Ejecutar solo un test específico
```bash
pytest tests/test_validaciones.py::test_validar_cedula_valida
```

### Ver cobertura de código (cuánto % está testeado)
```bash
pytest --cov=project --cov-report=html
```
Esto genera un reporte en `htmlcov/index.html`

---

## 📁 Estructura de Tests

```
proyecto/
├── project/              # Tu código
│   ├── app.py
│   └── utils/
│       └── validaciones.py
└── tests/                # Tus tests
    ├── __init__.py
    ├── test_validaciones.py
    └── test_decorators.py
```

**Convención**: Los archivos de test siempre empiezan con `test_`

---

## 📝 Escribiendo Tests

### Estructura básica
```python
def test_descripcion_de_lo_que_prueba():
    """Docstring explicando el test"""
    # 1. ARRANGE (Preparar)
    dato = "V-12345678"
    
    # 2. ACT (Actuar)
    resultado, error = validar_cedula(dato)
    
    # 3. ASSERT (Verificar)
    assert resultado == True
    assert error == None
```

### Tipos de asserts comunes
```python
# Igualdad
assert valor == 5

# Desigualdad
assert valor != 0

# Verdadero/Falso
assert es_valido == True
assert es_valido == False

# Contiene
assert "error" in mensaje

# Mayor/Menor
assert edad > 18
assert peso < 200

# Excepciones
with pytest.raises(ValueError):
    funcion_que_debe_fallar()
```

---

## 🎯 Casos que Debes Probar

Para cada función, prueba:

### ✅ **Caso feliz** (todo bien)
```python
def test_validar_email_valido():
    assert validar_email("juan@gmail.com")[0] == True
```

### ❌ **Caso de error** (entrada inválida)
```python
def test_validar_email_invalido():
    assert validar_email("no-es-email")[0] == False
```

### 🔄 **Casos límite** (edge cases)
```python
def test_validar_edad_minima():
    assert validar_edad("5")[0] == True  # Límite inferior

def test_validar_edad_maxima():
    assert validar_edad("100")[0] == True  # Límite superior
```

### ⚠️ **Casos especiales**
```python
def test_validar_email_vacio():
    assert validar_email("")[0] == False

def test_validar_email_none():
    assert validar_email(None)[0] == False
```

---

## 📊 Interpretando Resultados

### Salida exitosa
```
tests/test_validaciones.py::test_validar_cedula_valida PASSED     [ 10%]
tests/test_validaciones.py::test_validar_cedula_invalida PASSED   [ 20%]
...
======================== 29 passed in 0.45s ========================
```

### Salida con fallo
```
tests/test_validaciones.py::test_validar_cedula_invalida FAILED   [ 20%]

FAILED tests/test_validaciones.py::test_validar_cedula_invalida
    def test_validar_cedula_invalida():
        es_valido, error = validar_cedula("INVALID")
>       assert es_valido == False
E       AssertionError: assert True == False

```

---

## 🎨 Ejemplo Práctico - Para tu Proyecto

### Probar una función de validación
```python
# En project/utils/validaciones.py
def validar_cedula(cedula: str):
    if not cedula:
        return False, "La cédula es requerida"
    
    pattern = r'^[VEve]-?\d{7,8}$'
    if not re.match(pattern, cedula.upper()):
        return False, "Formato de cédula inválido"
    
    return True, None


# En tests/test_validaciones.py
def test_validar_cedula_valida():
    """Cédula V-12345678 debe ser válida"""
    es_valido, error = validar_cedula("V-12345678")
    assert es_valido == True
    assert error == None

def test_validar_cedula_invalida():
    """Cédula X-12345678 debe ser inválida"""
    es_valido, error = validar_cedula("X-12345678")
    assert es_valido == False
    assert "inválido" in error.lower()
```

---

## 💡 Mejores Prácticas

### ✅ DO (Hacer)
- ✅ Nombra los tests descriptivamente: `test_crear_atleta_con_datos_validos`
- ✅ Un test = Una cosa: No pruebes 10 cosas en un solo test
- ✅ Tests independientes: Cada test debe funcionar solo
- ✅ Documenta tests complejos con docstrings
- ✅ Usa fixtures para código repetitivo

### ❌ DON'T (No Hacer)
- ❌ Tests que dependen de otros tests
- ❌ Tests que modifican la base de datos real
- ❌ Tests lentos (> 1 segundo por test)
- ❌ Dejar código duplicado en tests

---

## 🔧 Tests Avanzados (Mocking)

Cuando necesitas probar código que usa Supabase sin conectarte realmente:

```python
from unittest.mock import patch, Mock

@patch('blueprints.dashboard.supabase')
def test_crear_atleta(mock_supabase):
    # Simular respuesta de Supabase
    mock_supabase.table().insert().execute.return_value = Mock(
        data=[{'id': 1, 'nombre': 'Juan'}]
    )
    
    # Ahora puedes probar la función sin tocar la BD real
    resultado = crear_atleta(datos)
    assert resultado['nombre'] == 'Juan'
```

---

## 📈 Cobertura de Código

### ¿Qué es?
El **porcentaje de código** que está siendo probado por tus tests.

### Objetivo
- 🎯 **60-70%**: Mínimo aceptable
- 🎯 **80-90%**: Muy bueno
- 🎯 **90-100%**: Excelente (pero a veces innecesario)

### Generar reporte de cobertura
```bash
pytest --cov=project --cov-report=html

# Abre htmlcov/index.html en el navegador
# Verás qué líneas están cubiertas (verde) y cuáles no (rojo)
```

---

## 🎯 Para tu Proyecto - Plan de Tests

### Prioridad Alta (Hacer primero)
1. ✅ **Validaciones** - `test_validaciones.py` (ya creado)
2. **Sanitización** - Probar que elimina scripts
3. **Upload de archivos** - Verificar validaciones de extensiones

### Prioridad Media
4. **Decoradores** - Login, admin, superadmin
5. **Queries a Supabase** - Con mocking
6. **Formularios** - Extracción de datos

### Prioridad Baja
7. **Rutas de app.py** - Login, registro, logout
8. **Dashboard routes** - CRUD de atletas
9. **Integración** - Tests end-to-end

---

## 🚀 Ejecutar Tests Automáticamente

### En cada commit (Git Hook)
Crea `.git/hooks/pre-commit`:
```bash
#!/bin/sh
pytest
if [ $? -ne 0 ]; then
    echo "❌ Tests fallaron. Commit cancelado."
    exit 1
fi
```

### En GitHub Actions (CI/CD)
Crea `.github/workflows/tests.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest
```

---

## 📚 Recursos para Aprender Más

- **Pytest Docs**: https://docs.pytest.org/
- **Real Python - Testing**: https://realpython.com/pytest-python-testing/
- **Test Driven Development**: Libro "Test Driven Development" by Kent Beck

---

## ❓ FAQ

### ¿Cuándo escribir tests?
**Idealmente**: Antes de escribir el código (TDD - Test Driven Development)
**Realisticamente**: Después de escribir funciones críticas

### ¿Necesito testear TODO?
No. Enfócate en:
- ✅ Lógica de negocio (validaciones, cálculos)
- ✅ Funciones críticas (autenticación, pagos)
- ⚠️ No tests para getters/setters triviales

### ¿Cuánto tiempo toma?
- Escribir test: 2-5 minutos
- Debuggear bug sin tests: 30-60 minutos

**Los tests ahorran tiempo a largo plazo** 📈

---

¡Empieza poco a poco y agrega tests gradualmente! 🎉
