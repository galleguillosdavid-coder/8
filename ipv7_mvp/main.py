"""
IPv7 Main - Punto de entrada simple
Ejecución: python main.py [--port PORT]
"""

import sys
import os

# Añadir directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from node import IPv7Node


def main():
    """Función principal"""
    port = 9000
    mtu = 1280
    node_id = None
    name = None
    
    # Parse argumentos simples
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--port" and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
                i += 2
            except ValueError:
                print("Invalid port number")
                return 1
        elif sys.argv[i] == "--mtu" and i + 1 < len(sys.argv):
            try:
                mtu = int(sys.argv[i + 1])
                i += 2
            except ValueError:
                print("Invalid MTU value")
                return 1
        elif sys.argv[i] == "--node-id" and i + 1 < len(sys.argv):
            try:
                node_id = int(sys.argv[i + 1])
                i += 2
            except ValueError:
                print("Invalid node-id value")
                return 1
        elif sys.argv[i] == "--name" and i + 1 < len(sys.argv):
            name = sys.argv[i + 1]
            i += 2
        else:
            try:
                # Si es solo un número, asumir que es el puerto
                port = int(sys.argv[i])
                i += 1
            except ValueError:
                print("Usage: python main.py [--port PORT] [--mtu MTU]")
                return 1
    
    print("=" * 50)
    print("IPv7 MVP - Minimum Viable Protocol")
    print("=" * 50)
    
    node = IPv7Node(port, mtu, name=name, node_id=node_id)
    
    try:
        node.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        node.stop()
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())