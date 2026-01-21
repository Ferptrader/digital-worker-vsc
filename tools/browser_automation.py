"""Browser Automation Tool - Automatiza navegação em sistemas farmacêuticos""" 
# from crewai_tools import BaseTool
from typing import Type, Optional, Any
from pydantic import BaseModel, Field
import time

class BrowserInput(BaseModel):
    """Input para BrowserTool"""
    action: str = Field(..., description="Ação: 'navigate', 'click', 'fill', 'extract', 'screenshot'")
    url: Optional[str] = Field(None, description="URL para navegar")
    selector: Optional[str] = Field(None, description="Seletor CSS do elemento")
    value: Optional[str] = Field(None, description="Valor para preencher")
    
