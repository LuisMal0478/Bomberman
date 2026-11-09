"""
Punto de entrada para la arquitectura MVC de Bomberman.
Utiliza ControladorMenu con la estructura modular (controladores, modelos, vistas, red).
"""

from controladores.controlador_menu import ControladorMenu


def main():
    menu = ControladorMenu()
    menu.ejecutar()


if __name__ == "__main__":
    main()

