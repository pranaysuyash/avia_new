"""
White-Label Customization System

Allows enterprise customers to customize the platform with their branding
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, HttpUrl, Field, validator, EmailStr
import json
import os
from pathlib import Path

class CustomizationLevel(str, Enum):
    """Levels of white-label customization"""
    BASIC = "basic"  # Logo and colors
    STANDARD = "standard"  # Basic + custom domain
    ADVANCED = "advanced"  # Standard + full UI customization
    ENTERPRISE = "enterprise"  # Complete white-label solution

class ColorScheme(BaseModel):
    """Brand color scheme"""
    primary: str = Field(regex="^#[0-9A-Fa-f]{6}$")
    secondary: str = Field(regex="^#[0-9A-Fa-f]{6}$")
    accent: str = Field(regex="^#[0-9A-Fa-f]{6}$")
    background: str = Field(regex="^#[0-9A-Fa-f]{6}$")
    text: str = Field(regex="^#[0-9A-Fa-f]{6}$")
    
    # Additional colors
    success: str = Field(default="#28a745", regex="^#[0-9A-Fa-f]{6}$")
    warning: str = Field(default="#ffc107", regex="^#[0-9A-Fa-f]{6}$")
    error: str = Field(default="#dc3545", regex="^#[0-9A-Fa-f]{6}$")
    info: str = Field(default="#17a2b8", regex="^#[0-9A-Fa-f]{6}$")

class Typography(BaseModel):
    """Brand typography settings"""
    font_family: str = "Inter, sans-serif"
    heading_font: Optional[str] = None
    font_size_base: int = 16
    line_height_base: float = 1.5
    
    # Font weights
    font_weight_normal: int = 400
    font_weight_medium: int = 500
    font_weight_bold: int = 700

class LogoAssets(BaseModel):
    """Brand logo assets"""
    primary_logo_url: HttpUrl
    primary_logo_dark_url: Optional[HttpUrl]
    favicon_url: HttpUrl
    
    # Additional logos
    square_logo_url: Optional[HttpUrl]
    email_logo_url: Optional[HttpUrl]
    
    # Dimensions
    logo_height: int = 40
    logo_max_width: int = 200

class CustomDomain(BaseModel):
    """Custom domain configuration"""
    domain: str
    subdomain: Optional[str] = "app"
    
    # SSL configuration
    ssl_certificate: Optional[str]
    ssl_private_key: Optional[str]
    ssl_auto_renew: bool = True
    
    # DNS settings
    dns_configured: bool = False
    dns_verification_token: Optional[str]
    
    @property
    def full_domain(self) -> str:
        if self.subdomain:
            return f"{self.subdomain}.{self.domain}"
        return self.domain

class EmailCustomization(BaseModel):
    """Email template customization"""
    from_name: str
    from_email: EmailStr
    reply_to_email: Optional[EmailStr]
    
    # Email footer
    company_name: str
    company_address: Optional[str]
    unsubscribe_url: Optional[HttpUrl]
    
    # Custom templates
    use_custom_templates: bool = False
    header_html: Optional[str]
    footer_html: Optional[str]

class UICustomization(BaseModel):
    """UI customization options"""
    # Navigation
    hide_platform_branding: bool = False
    custom_navigation_items: List[Dict[str, str]] = []
    
    # Features
    hidden_features: List[str] = []
    custom_feature_names: Dict[str, str] = {}
    
    # Layout
    sidebar_position: str = "left"  # left, right
    compact_mode: bool = False
    
    # Custom components
    custom_css: Optional[str]
    custom_javascript: Optional[str]
    
    # Login page
    login_background_image: Optional[HttpUrl]
    login_welcome_message: Optional[str]

class WhiteLabelConfig(BaseModel):
    """Complete white-label configuration"""
    organization_id: str
    customization_level: CustomizationLevel
    
    # Branding
    brand_name: str
    brand_tagline: Optional[str]
    
    # Visual customization
    colors: ColorScheme
    typography: Typography
    logos: LogoAssets
    
    # Domain
    custom_domain: Optional[CustomDomain]
    
    # Email
    email_customization: EmailCustomization
    
    # UI
    ui_customization: UICustomization
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    # Validation
    @validator('custom_domain')
    def validate_domain_level(cls, v, values):
        """Ensure custom domain is only for appropriate levels"""
        if v and values.get('customization_level') == CustomizationLevel.BASIC:
            raise ValueError("Custom domain not available for Basic level")
        return v

class WhiteLabelManager:
    """Manages white-label customizations"""
    
    def __init__(self, storage_path: str = "./white_label_configs"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.configs: Dict[str, WhiteLabelConfig] = {}
        self._load_configs()
    
    def _load_configs(self):
        """Load existing configurations"""
        for config_file in self.storage_path.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    config = WhiteLabelConfig(**data)
                    self.configs[config.organization_id] = config
            except Exception as e:
                print(f"Error loading config {config_file}: {e}")
    
    def create_config(
        self,
        organization_id: str,
        brand_name: str,
        customization_level: CustomizationLevel,
        **kwargs
    ) -> WhiteLabelConfig:
        """Create new white-label configuration"""
        # Set defaults based on level
        defaults = self._get_level_defaults(customization_level)
        
        # Merge with provided values
        config_data = {
            "organization_id": organization_id,
            "brand_name": brand_name,
            "customization_level": customization_level,
            **defaults,
            **kwargs
        }
        
        config = WhiteLabelConfig(**config_data)
        
        # Save configuration
        self.save_config(config)
        
        return config
    
    def _get_level_defaults(self, level: CustomizationLevel) -> Dict[str, Any]:
        """Get default configuration for customization level"""
        defaults = {
            "colors": ColorScheme(
                primary="#007bff",
                secondary="#6c757d",
                accent="#28a745",
                background="#ffffff",
                text="#212529"
            ),
            "typography": Typography(),
            "logos": LogoAssets(
                primary_logo_url="https://placeholder.com/logo.png",
                favicon_url="https://placeholder.com/favicon.ico"
            ),
            "email_customization": EmailCustomization(
                from_name="Transcription Platform",
                from_email="noreply@transcription.com",
                company_name="Your Company"
            ),
            "ui_customization": UICustomization()
        }
        
        # Add level-specific features
        if level in [CustomizationLevel.ADVANCED, CustomizationLevel.ENTERPRISE]:
            defaults["ui_customization"].hide_platform_branding = True
        
        return defaults
    
    def save_config(self, config: WhiteLabelConfig):
        """Save configuration to storage"""
        self.configs[config.organization_id] = config
        
        config_file = self.storage_path / f"{config.organization_id}.json"
        with open(config_file, 'w') as f:
            json.dump(config.dict(), f, indent=2, default=str)
    
    def get_config(self, organization_id: str) -> Optional[WhiteLabelConfig]:
        """Get configuration for organization"""
        return self.configs.get(organization_id)
    
    def update_config(
        self,
        organization_id: str,
        updates: Dict[str, Any]
    ) -> WhiteLabelConfig:
        """Update existing configuration"""
        config = self.get_config(organization_id)
        if not config:
            raise ValueError(f"No configuration found for {organization_id}")
        
        # Update fields
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        config.updated_at = datetime.utcnow()
        
        # Save updated config
        self.save_config(config)
        
        return config
    
    def generate_css(self, config: WhiteLabelConfig) -> str:
        """Generate CSS based on configuration"""
        css_template = f"""
/* White-label customization for {config.brand_name} */

:root {{
    /* Brand Colors */
    --primary-color: {config.colors.primary};
    --secondary-color: {config.colors.secondary};
    --accent-color: {config.colors.accent};
    --background-color: {config.colors.background};
    --text-color: {config.colors.text};
    
    --success-color: {config.colors.success};
    --warning-color: {config.colors.warning};
    --error-color: {config.colors.error};
    --info-color: {config.colors.info};
    
    /* Typography */
    --font-family: {config.typography.font_family};
    --heading-font: {config.typography.heading_font or config.typography.font_family};
    --font-size-base: {config.typography.font_size_base}px;
    --line-height-base: {config.typography.line_height_base};
    
    --font-weight-normal: {config.typography.font_weight_normal};
    --font-weight-medium: {config.typography.font_weight_medium};
    --font-weight-bold: {config.typography.font_weight_bold};
}}

/* Base styles */
body {{
    font-family: var(--font-family);
    font-size: var(--font-size-base);
    line-height: var(--line-height-base);
    color: var(--text-color);
    background-color: var(--background-color);
}}

h1, h2, h3, h4, h5, h6 {{
    font-family: var(--heading-font);
    font-weight: var(--font-weight-bold);
}}

/* Primary button */
.btn-primary {{
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}}

.btn-primary:hover {{
    background-color: color-mix(in srgb, var(--primary-color) 85%, black);
    border-color: color-mix(in srgb, var(--primary-color) 85%, black);
}}

/* Logo */
.brand-logo {{
    height: {config.logos.logo_height}px;
    max-width: {config.logos.logo_max_width}px;
}}

/* Custom CSS */
{config.ui_customization.custom_css or ''}
"""
        
        return css_template
    
    def generate_email_template(
        self,
        config: WhiteLabelConfig,
        content: str
    ) -> str:
        """Generate email template with branding"""
        header = config.email_customization.header_html or f"""
        <div style="background-color: {config.colors.primary}; padding: 20px; text-align: center;">
            <img src="{config.logos.email_logo_url or config.logos.primary_logo_url}" 
                 alt="{config.brand_name}" 
                 style="height: 50px;">
        </div>
        """
        
        footer = config.email_customization.footer_html or f"""
        <div style="background-color: #f8f9fa; padding: 20px; text-align: center; margin-top: 40px;">
            <p style="color: #6c757d; font-size: 14px; margin: 0;">
                © {datetime.now().year} {config.email_customization.company_name}
            </p>
            {f'<p style="color: #6c757d; font-size: 12px; margin: 10px 0 0 0;">{config.email_customization.company_address}</p>' if config.email_customization.company_address else ''}
        </div>
        """
        
        return f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: {config.typography.font_family};
                    color: {config.colors.text};
                    line-height: 1.6;
                }}
                a {{
                    color: {config.colors.primary};
                }}
            </style>
        </head>
        <body>
            {header}
            <div style="padding: 40px 20px; max-width: 600px; margin: 0 auto;">
                {content}
            </div>
            {footer}
        </body>
        </html>
        """
    
    def validate_domain(self, config: WhiteLabelConfig) -> Dict[str, Any]:
        """Validate custom domain configuration"""
        if not config.custom_domain:
            return {"valid": False, "error": "No custom domain configured"}
        
        # In production, this would:
        # 1. Check DNS records
        # 2. Validate SSL certificate
        # 3. Test domain accessibility
        
        return {
            "valid": True,
            "domain": config.custom_domain.full_domain,
            "ssl_valid": bool(config.custom_domain.ssl_certificate),
            "dns_configured": config.custom_domain.dns_configured
        }
    
    def export_config(
        self,
        organization_id: str,
        format: str = "json"
    ) -> str:
        """Export configuration for deployment"""
        config = self.get_config(organization_id)
        if not config:
            raise ValueError(f"No configuration found for {organization_id}")
        
        if format == "json":
            return json.dumps(config.dict(), indent=2, default=str)
        elif format == "env":
            return self._generate_env_vars(config)
        elif format == "nginx":
            return self._generate_nginx_config(config)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_env_vars(self, config: WhiteLabelConfig) -> str:
        """Generate environment variables"""
        env_vars = f"""
# White-label configuration for {config.brand_name}
WHITE_LABEL_ENABLED=true
WHITE_LABEL_ORG_ID={config.organization_id}
WHITE_LABEL_BRAND_NAME={config.brand_name}
WHITE_LABEL_PRIMARY_COLOR={config.colors.primary}
WHITE_LABEL_CUSTOM_DOMAIN={config.custom_domain.full_domain if config.custom_domain else ''}
WHITE_LABEL_HIDE_BRANDING={str(config.ui_customization.hide_platform_branding).lower()}
"""
        return env_vars
    
    def _generate_nginx_config(self, config: WhiteLabelConfig) -> str:
        """Generate nginx configuration for custom domain"""
        if not config.custom_domain:
            return "# No custom domain configured"
        
        return f"""
server {{
    listen 80;
    listen [::]:80;
    server_name {config.custom_domain.full_domain};
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {config.custom_domain.full_domain};
    
    # SSL configuration
    ssl_certificate /etc/ssl/certs/{config.organization_id}.crt;
    ssl_certificate_key /etc/ssl/private/{config.organization_id}.key;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # White-label headers
    add_header X-Organization-ID "{config.organization_id}" always;
    
    location / {{
        proxy_pass http://app_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Organization-ID "{config.organization_id}";
    }}
}}
"""

class WhiteLabelPreview:
    """Generate preview of white-label customization"""
    
    @staticmethod
    def generate_preview_html(config: WhiteLabelConfig) -> str:
        """Generate HTML preview of customization"""
        manager = WhiteLabelManager()
        css = manager.generate_css(config)
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.brand_name} - White Label Preview</title>
    <style>
        {css}
        
        .preview-container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .preview-section {{
            margin-bottom: 40px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }}
        
        .color-swatch {{
            display: inline-block;
            width: 50px;
            height: 50px;
            margin: 5px;
            border-radius: 4px;
            vertical-align: middle;
        }}
        
        .button-preview {{
            margin: 5px;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-family: var(--font-family);
        }}
    </style>
</head>
<body>
    <div class="preview-container">
        <h1>{config.brand_name} - White Label Preview</h1>
        {f'<p>{config.brand_tagline}</p>' if config.brand_tagline else ''}
        
        <div class="preview-section">
            <h2>Brand Colors</h2>
            <div>
                <span class="color-swatch" style="background-color: {config.colors.primary}"></span> Primary
                <span class="color-swatch" style="background-color: {config.colors.secondary}"></span> Secondary
                <span class="color-swatch" style="background-color: {config.colors.accent}"></span> Accent
                <span class="color-swatch" style="background-color: {config.colors.success}"></span> Success
                <span class="color-swatch" style="background-color: {config.colors.error}"></span> Error
            </div>
        </div>
        
        <div class="preview-section">
            <h2>Typography</h2>
            <h1>Heading 1</h1>
            <h2>Heading 2</h2>
            <h3>Heading 3</h3>
            <p>This is a paragraph with the configured font family and base font size.</p>
            <p><strong>Bold text</strong> and <em>italic text</em> examples.</p>
        </div>
        
        <div class="preview-section">
            <h2>Buttons</h2>
            <button class="button-preview btn-primary" style="background-color: var(--primary-color); color: white;">
                Primary Button
            </button>
            <button class="button-preview" style="background-color: var(--secondary-color); color: white;">
                Secondary Button
            </button>
            <button class="button-preview" style="background-color: var(--success-color); color: white;">
                Success Button
            </button>
            <button class="button-preview" style="background-color: var(--error-color); color: white;">
                Error Button
            </button>
        </div>
        
        <div class="preview-section">
            <h2>Logo</h2>
            <img src="{config.logos.primary_logo_url}" alt="{config.brand_name}" class="brand-logo">
        </div>
        
        <div class="preview-section">
            <h2>Configuration Details</h2>
            <ul>
                <li>Customization Level: <strong>{config.customization_level.value}</strong></li>
                <li>Custom Domain: <strong>{config.custom_domain.full_domain if config.custom_domain else 'Not configured'}</strong></li>
                <li>Hide Platform Branding: <strong>{'Yes' if config.ui_customization.hide_platform_branding else 'No'}</strong></li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

# Example usage
if __name__ == "__main__":
    manager = WhiteLabelManager()
    
    # Create a white-label configuration
    config = manager.create_config(
        organization_id="acme_corp",
        brand_name="Acme Transcription",
        customization_level=CustomizationLevel.ADVANCED,
        brand_tagline="Enterprise Speech Intelligence",
        colors=ColorScheme(
            primary="#1a73e8",
            secondary="#5f6368",
            accent="#34a853",
            background="#ffffff",
            text="#202124"
        ),
        custom_domain=CustomDomain(
            domain="acme.com",
            subdomain="transcribe"
        )
    )
    
    # Generate CSS
    css = manager.generate_css(config)
    print("Generated CSS preview...")
    
    # Generate preview
    preview = WhiteLabelPreview.generate_preview_html(config)
    
    # Save preview
    with open("white_label_preview.html", "w") as f:
        f.write(preview)
    print("Preview saved to white_label_preview.html")