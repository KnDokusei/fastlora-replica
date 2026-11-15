"""Genera presentacion_avance.pdfpc: notas del orador que pdfpc muestra solo en la consola.

Cada línea con guion es texto para decir tal cual. Las acciones van entre corchetes y en cursiva.
Después de editar: cerrar pdfpc, correr `python3 generar_notas_pdfpc.py` y volver a abrir pdfpc.
"""
import json


def accion(texto):
    return f"*[{texto}]*"


# (título, tiempo, minuto acumulado, [líneas]); las líneas que empiezan con "*[" son acciones
NOTAS = [
    ("Portada", "20 s", "0:20", [
        "En quince minutos van a saber por qué un paquete LoRa llega o se pierde, y cómo decidir si un simulador que calcula eso en milisegundos dice la verdad.",
        "Mi proyecto es replicar la validación de FAST-LoRa, un simulador publicado este año en IEEE Access.",
        accion("avanzar"),
    ]),
    ("Problema", "60 s", "1:20", [
        "Imaginen cien sensores en un campo. Cada uno elige un spreading factor, entre seis, y una potencia, entre ocho: cuarenta y ocho opciones por sensor.",
        "Eso da cuarenta y ocho elevado a cien redes posibles, más o menos diez elevado a ciento sesenta y ocho.",
        "¿Cuánto creen que se demora evaluar una sola?",
        accion("esperar 5 segundos en silencio"),
        "Con FLoRa, que simula paquete a paquete, más de cinco minutos. Con FAST-LoRa, menos de ocho milisegundos.",
        "Para optimizar una red se necesitan miles de evaluaciones: diez mil son más de un mes en FLoRa y poco más de un minuto en FAST-LoRa.",
    ]),
    ("Sin embargo", "70 s", "2:30", [
        "Eso es lo que promete el paper: hasta mil veces más rápido, con un error de 0,94 puntos en la PDR, que es la fracción de paquetes que llegan, y de 0,04 bits por milijoule en energía.",
        "Sin embargo, lo validaron solo sus autores, contra un FLoRa que ellos mismos modificaron, con el ADR apagado, que es justamente el ajuste automático que la herramienta promete evaluar, y con números que no calzan, que les mostraré más adelante.",
        accion("mirar al público"),
        "Si el modelo se equivoca, también se equivocan las redes que se diseñen con él.",
    ]),
    ("Promesa", "25 s", "2:55", [
        "Al terminar van a saber cuándo creerle a un simulador de ocho milisegundos.",
        "Voy en tres partes: primero los conceptos, después el estado del arte y al final mi objetivo. Arriba a la derecha siempre se ve en qué parte vamos.",
    ]),
    ("LoRaWAN", "60 s", "3:55", [
        "Partamos con un ejemplo: un sensor de riego que envía diez bytes cada diecisiete minutos.",
        accion("señalar el 1"),
        "El sensor transmite cuando tiene un dato, sin escuchar si el canal está libre. Es ALOHA puro, lo que vimos en el curso, que aprovecha como máximo un 18 % del canal.",
        accion("señalar el 2"),
        "El mismo paquete puede llegar a dos gateways, y basta con que uno lo reciba.",
        accion("señalar el 3"),
        "El servidor de red descarta los duplicados y ajusta el SF y la potencia de cada nodo. Eso es el ADR.",
        "¿Y qué es el SF?",
    ]),
    ("Spreading factor", "50 s", "4:45", [
        "El spreading factor define cuánto dura cada símbolo: cada SF extra lo hace dos veces más largo.",
        "Para un paquete de diez bytes, pasar de SF7 a SF12 significa veintisiete veces más tiempo en el aire: más energía y más probabilidad de chocar.",
        "A cambio, con SF12 el receptor entiende una señal cien veces más débil que el ruido.",
    ]),
    ("Llega débil", "45 s", "5:30", [
        "Un paquete se puede perder por dos razones. La primera es que llegue débil.",
        "La potencia que llega baja con la distancia y además varía al azar en cada paquete; por eso la dibujo como una campana.",
        "Lo que queda a la derecha de la sensibilidad del receptor llega: esa área es la probabilidad psi. Lo que queda a la izquierda se pierde.",
    ]),
    ("Choca", "60 s", "6:30", [
        "La segunda razón es que choque con otro paquete.",
        "Si el paquete B pisa los últimos cinco símbolos del preámbulo de A, y A no llega al menos seis decibeles más fuerte, A se pierde.",
        "Si usan SF distintos casi siempre sobrevive, porque los SF se interfieren poco.",
        "La probabilidad de no chocar es zeta. Entonces la PDR es psi por zeta: llegar con fuerza suficiente, por no chocar. Y con varios gateways basta con que uno lo reciba.",
    ]),
    ("Simular vs calcular", "45 s", "7:15", [
        "Esta es la idea central: FLoRa cuenta paquetes, FAST-LoRa calcula probabilidades.",
        "FLoRa genera cada paquete durante cinco días simulados, unos 432 por nodo, y cuenta cuántos llegan.",
        "FAST-LoRa calcula psi y zeta para todos los nodos de una vez.",
        "Es la diferencia entre lanzar una moneda mil veces o calcular que la probabilidad es un medio.",
        "Eso sí, FAST-LoRa no modela la bajada ni varios canales, y supone tráfico estable.",
        accion("control: deberían ir unos 7 minutos"),
    ]),
    ("Mapa", "60 s", "8:15", [
        "Pasemos al estado del arte. Las herramientas para LoRa van desde una fórmula cerrada hasta una red real.",
        "A la izquierda están ALOHA y los modelos de geometría estocástica, que responden por una red promedio.",
        "Al medio, los modelos por dispositivo, como el de Toro-Betancur y FAST-LoRa.",
        "A la derecha, los simuladores paquete a paquete: LoRaSim, ns-3 y FLoRa. Mientras más detalle, más caro.",
        "Yo voy a comparar FAST-LoRa contra FLoRa. Y un dato: FAST-LoRa tiene cuatro citas, tres del mismo grupo, y ninguna réplica independiente.",
    ]),
    ("Lecturas", "55 s", "9:10", [
        "De lo que he leído, me quedo con tres cosas.",
        "De Bor y colegas salen los parámetros de propagación que usan FLoRa y FAST-LoRa, medidos en Lancaster.",
        "Croce mostró que los SF se interfieren un poco entre sí, y de ahí salen los umbrales.",
        "Y lo más importante: Toro-Betancur ya había publicado este mismo modelo en 2021. FAST-LoRa lo toma a través de Zhang, en 2023.",
    ]),
    ("Cabos sueltos", "70 s", "10:20", [
        "Leí el paper con calculadora en mano y encontré cuatro cosas.",
        "Uno: el paper nunca dice el tamaño del paquete. Lo encontré en el código: diez bytes.",
        "Dos: el error se promedia de dos formas distintas, 0,040 por nodo y 0,038 por tabla.",
        "Tres: con sus propios tiempos la aceleración es de unas diez mil veces, no mil.",
        "Cuatro: la ecuación 11 usa dos sigma donde corresponde raíz de dos por sigma.",
    ]),
    ("Código", "65 s", "11:25", [
        "Como faltaba el tamaño del paquete, fui al código.",
        "Los experimentos no están en el repositorio que cita el paper, sino en otro del mismo autor, junto con su versión modificada de FLoRa.",
        "Ahí aparece que los dos simuladores no calculan igual el tiempo en el aire, que usan umbrales distintos para paquetes del mismo SF, seis contra un decibel, que la matriz de umbrales está al revés en el código y que el código del ADR falla.",
        "Con el tráfico que usan, algunas diferencias pesan poco. Medir cuánto pesa cada una es justamente lo que aporta una réplica.",
    ]),
    ("Objetivo", "50 s", "12:15", [
        "Mi objetivo para el semestre es repetir la validación por mi cuenta.",
        "La misma topología entra a los dos simuladores, de ambos saco la PDR y la energía por nodo, calculo el error entre ellos y lo comparo con el del paper.",
        "El criterio de éxito lo fijé antes de simular: mismas tendencias y un error del mismo orden. Si no calza, explicar por qué también es un resultado.",
        "Si queda tiempo, lo repito con el ADR encendido.",
        accion("control: si van más de 13:15, saltar la lámina 16"),
    ]),
    ("Resultado", "50 s", "13:05", [
        "En la presentación final van a ver esta figura y esta tabla, hechas por mí.",
        "La figura es el caso más simple: un nodo y un gateway, la PDR según el SF.",
        "La tabla es el error en redes densas, hasta quinientos nodos y cuatro gateways. El valor en naranjo es el peor caso.",
        "Y además, los tiempos de cómputo.",
    ]),
    ("Plan (saltable)", "25 s", "13:30", [
        "El plan tiene tres etapas. Hasta el 8 de noviembre instalo el FLoRa de los autores y corro el primer experimento. Hasta el 20, los experimentos dos y tres. Y hasta el 1 de diciembre, la comparación, el informe y el repositorio.",
        "El riesgo principal es que ese FLoRa es una versión antigua, la 1.1.0, así que voy a instalar justo las versiones que pide: OMNeT++ 6.0 e INET 4.4.",
    ]),
    ("Referencias", "10 s", "13:40", [
        "Estas son las referencias; cada afirmación de las láminas lleva su número.",
    ]),
    ("Cierre", "40 s", "14:20", [
        "Si se quedan con una sola idea, que sea esta: FAST-LoRa calcula en milisegundos lo que FLoRa simula en minutos, pero antes de diseñar redes con él hay que verificarlo por fuera.",
        "Hay que creerle lo suficiente para usarlo y dudar lo suficiente para verificarlo.",
        "En este avance expliqué el modelo desde cero, armé el mapa del estado del arte, encontré cabos sueltos en el paper y en el código, y dejé un método con un criterio de éxito fijado de antemano.",
        "Quedo atento a sus comentarios, sobre todo si alguno ha usado FLoRa.",
        accion("no avanzar: dejar esta lámina durante las preguntas"),
    ]),
    ("Respaldo: parámetros", "preguntas", "-", [
        "Todos los parámetros salen de las tablas 1 a 3 del paper. El único que falta es el tamaño del paquete, que en el código es de diez bytes.",
        accion("para volver al cierre: g, 18, Enter"),
    ]),
    ("Respaldo: código", "preguntas", "-", [
        "Esta es la lista completa de diferencias. Los repositorios son FastLoRa y MultiAgent-MARLTC, del mismo autor.",
        "Con un paquete cada mil segundos, la probabilidad de que dos nodos se traslapen es menor a 0,2 %, por eso algunas diferencias pesan poco.",
        accion("para volver al cierre: g, 18, Enter"),
    ]),
    ("Respaldo: ecuación 11", "preguntas", "-", [
        "Si resto dos ruidos gaussianos independientes, cada uno con desviación sigma, las varianzas se suman: queda dos sigma al cuadrado, o sea desviación raíz de dos por sigma.",
        "El paper y el código usan dos sigma, que corresponde a varianza cuatro sigma al cuadrado.",
        accion("para volver al cierre: g, 18, Enter"),
    ]),
    ("Respaldo: Packet Tracer", "preguntas", "-", [
        "Packet Tracer y GNS3 emulan redes IP, pero no modelan la capa física de LoRa: ni el SF, ni el tiempo en el aire, ni los choques por radio. FLoRa y ns-3 sí.",
        accion("para volver al cierre: g, 18, Enter"),
    ]),
    ("Respaldo: tiempo en el aire", "preguntas", "-", [
        "El tiempo en el aire depende mucho del tamaño del paquete: casi se duplica entre 20 y 51 bytes. Por eso importa que el paper no lo informe.",
        accion("para volver al cierre: g, 18, Enter"),
    ]),
]

pages = []
for i, (titulo, tiempo, llevo, lineas) in enumerate(NOTAS):
    cuerpo = "\n".join(l if l.startswith("*[") else f"- {l}" for l in lineas)
    texto = f"**{i + 1} · {titulo}** · {tiempo} · llevo {llevo}\n\n{cuerpo}"
    pages.append({"idx": i, "label": str(i + 1), "note": texto})

data = {"pdfpcFormat": 2, "duration": 15, "disableMarkdown": False, "noteFontSize": 20, "pages": pages}
with open("presentacion_avance.pdfpc", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print(f"{len(pages)} notas escritas")
