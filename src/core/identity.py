"""
IPv7 Identity Management
Handles DID (Decentralized Identifier) generation and persistence
"""

import json
import os
import random
import string
from typing import Optional


class IdentityManager:
    """Manages IPv7 decentralized identities (DIDs)"""
    
    @staticmethod
    def generate_did(length: int = 8) -> str:
        """Generate a random DID suffix"""
        sufijo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        return f"did:ipv7:{sufijo}"
    
    @staticmethod
    def get_or_create(identity_file: str = "ipv7_identidad.json") -> str:
        """
        Load existing DID from file or create a new one
        
        Args:
            identity_file: Path to the identity JSON file
            
        Returns:
            The DID string
        """
        if os.path.exists(identity_file):
            try:
                with open(identity_file, "r") as f:
                    datos = json.load(f)
                    return datos["did"]
            except (json.JSONDecodeError, KeyError):
                # File corrupted, regenerate
                pass
        
        # Generate new DID
        nuevo_did = IdentityManager.generate_did()
        
        with open(identity_file, "w") as f:
            json.dump({"did": nuevo_did}, f)
        
        return nuevo_did
    
    @staticmethod
    def get_or_create_for_port(port: int) -> str:
        """
        Get or create identity specific to a port
        
        Args:
            port: The port number for this identity
            
        Returns:
            The DID string
        """
        identity_file = f"ipv7_identidad_{port}.json"
        return IdentityManager.get_or_create(identity_file)