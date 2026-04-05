# 🎨 CONSTANTES DE CONFIGURACIÓN VISUAL Y DE NEGOCIO

# Colores semánticos para estados de cumplimiento (accesibles y consistentes)
COLOR_CUMPLE = '#22c55e'      # Verde: pedido cumplido dentro de SLA
COLOR_NO_CUMPLE = '#ef4444'   # Rojo: pedido fuera de SLA
COLOR_PTE = '#f59e0b'         # Ámbar: pedido pendiente (PTE)
COLOR_PRIMARY = '#6366f1'     # Índigo: color principal de la marca

# Plantilla de Plotly para modo oscuro (coherente con el diseño)
PLOTLY_TEMPLATE = 'plotly_dark'

# Umbrales de negocio para alertas automáticas (configurables)
UMBRALES_ALERTAS = {
    'cumplimiento_minimo': 95.0,      # % mínimo de cumplimiento para alerta
    'desvio_entrega_max': 5.0,        # Días máximos de desvío promedio
    'transportadora_min_perf': 60.0,  # % mínimo de desempeño por transportadora
    'pendientes_max': 10              # Máximo de pedidos PTE antes de alertar
}
