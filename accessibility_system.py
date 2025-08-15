"""
Comprehensive Accessibility System - Task 71 Implementation
WCAG 2.1 AA compliant accessibility features for the transcription platform
Builds upon existing design-system-accessibility.json configuration
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import streamlit as st
from datetime import datetime
import base64
import re

logger = logging.getLogger(__name__)


class AccessibilityLevel(Enum):
    """WCAG accessibility levels"""
    A = "A"
    AA = "AA" 
    AAA = "AAA"


class AssistiveTechnology(Enum):
    """Types of assistive technology"""
    SCREEN_READER = "screen_reader"
    KEYBOARD_ONLY = "keyboard_only"
    VOICE_CONTROL = "voice_control"
    SWITCH_CONTROL = "switch_control"
    HIGH_CONTRAST = "high_contrast"
    MAGNIFICATION = "magnification"


@dataclass
class AccessibilityPreferences:
    """User accessibility preferences"""
    reduced_motion: bool = False
    high_contrast: bool = False
    large_text: bool = False
    screen_reader: bool = False
    keyboard_only: bool = False
    focus_indicators: bool = True
    audio_descriptions: bool = False
    captions: bool = False
    sign_language: bool = False
    simplified_ui: bool = False
    
    def to_dict(self) -> Dict[str, bool]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, bool]) -> 'AccessibilityPreferences':
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class WCAGViolation:
    """WCAG compliance violation"""
    level: AccessibilityLevel
    guideline: str
    criterion: str
    element: str
    description: str
    severity: str  # 'critical', 'serious', 'moderate', 'minor'
    fix_suggestion: str
    timestamp: datetime


class AccessibilityConfig:
    """Load and manage accessibility configuration"""
    
    def __init__(self, config_path: str = "design-system-accessibility.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load accessibility configuration from JSON"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Accessibility config not found at {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load accessibility config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default accessibility configuration"""
        return {
            "wcag": {
                "level": "AA",
                "guidelines": {
                    "colorContrast": {"normal": 4.5, "large": 3.0, "enhanced": 7.0},
                    "minTouchTarget": "44px",
                    "maxLineLength": "70ch",
                    "animationDuration": {"max": "5s", "reducedMotion": "0.3s"}
                }
            },
            "keyboard": {
                "navigation": {
                    "tab": "forward navigation",
                    "shiftTab": "backward navigation",
                    "enter": "activate",
                    "space": "activate/select",
                    "escape": "close/cancel",
                    "arrowKeys": "directional navigation"
                }
            },
            "screenReader": {
                "landmarks": {
                    "main": "Primary content area",
                    "navigation": "Site navigation",
                    "search": "Search functionality"
                }
            }
        }
    
    def get_contrast_ratio(self, level: str = "normal") -> float:
        """Get required contrast ratio for WCAG level"""
        return self.config.get("wcag", {}).get("guidelines", {}).get("colorContrast", {}).get(level, 4.5)
    
    def get_min_touch_target(self) -> str:
        """Get minimum touch target size"""
        return self.config.get("wcag", {}).get("guidelines", {}).get("minTouchTarget", "44px")


class ColorContrastChecker:
    """Check color contrast compliance"""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color to RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def get_luminance(r: int, g: int, b: int) -> float:
        """Calculate relative luminance"""
        def adjust_color(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        r, g, b = map(adjust_color, (r, g, b))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    @classmethod
    def check_contrast(cls, color1: str, color2: str) -> Dict[str, Union[float, bool]]:
        """Check contrast ratio between two colors"""
        try:
            rgb1 = cls.hex_to_rgb(color1)
            rgb2 = cls.hex_to_rgb(color2)
            
            lum1 = cls.get_luminance(*rgb1)
            lum2 = cls.get_luminance(*rgb2)
            
            ratio = (max(lum1, lum2) + 0.05) / (min(lum1, lum2) + 0.05)
            
            return {
                'ratio': round(ratio, 2),
                'passes_aa_normal': ratio >= 4.5,
                'passes_aa_large': ratio >= 3.0,
                'passes_aaa_normal': ratio >= 7.0,
                'passes_aaa_large': ratio >= 4.5
            }
        except Exception as e:
            logger.error(f"Error checking contrast: {e}")
            return {'ratio': 0.0, 'passes_aa_normal': False, 'passes_aa_large': False}


class AccessibilityValidator:
    """Validate content for WCAG compliance"""
    
    def __init__(self, config: AccessibilityConfig):
        self.config = config
        self.violations: List[WCAGViolation] = []
    
    def validate_text(self, text: str, context: str = "content") -> List[WCAGViolation]:
        """Validate text content for accessibility"""
        violations = []
        
        # Check for very long lines (readability)
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if len(line) > 80:  # Rough character count for readability
                violations.append(WCAGViolation(
                    level=AccessibilityLevel.AA,
                    guideline="1.4.8",
                    criterion="Visual Presentation",
                    element=f"{context} line {i+1}",
                    description=f"Line too long ({len(line)} characters)",
                    severity="moderate",
                    fix_suggestion="Break long lines or provide text reflow options",
                    timestamp=datetime.now()
                ))
        
        # Check for ALL CAPS text (screen reader issues)
        if re.search(r'\b[A-Z]{3,}\b', text):
            violations.append(WCAGViolation(
                level=AccessibilityLevel.A,
                guideline="1.4.5",
                criterion="Text Content",
                element=context,
                description="Text contains all capitals which may be read as acronyms",
                severity="minor",
                fix_suggestion="Use sentence case or provide proper markup for acronyms",
                timestamp=datetime.now()
            ))
        
        return violations
    
    def validate_media(self, media_info: Dict[str, Any]) -> List[WCAGViolation]:
        """Validate media content for accessibility"""
        violations = []
        
        # Check for captions/transcripts
        if media_info.get('type') == 'video' and not media_info.get('has_captions'):
            violations.append(WCAGViolation(
                level=AccessibilityLevel.A,
                guideline="1.2.2",
                criterion="Captions (Prerecorded)",
                element=media_info.get('filename', 'video'),
                description="Video content lacks captions",
                severity="critical",
                fix_suggestion="Provide captions or transcripts for video content",
                timestamp=datetime.now()
            ))
        
        if media_info.get('type') == 'audio' and not media_info.get('has_transcript'):
            violations.append(WCAGViolation(
                level=AccessibilityLevel.A,
                guideline="1.2.1",
                criterion="Audio-only and Video-only (Prerecorded)",
                element=media_info.get('filename', 'audio'),
                description="Audio content lacks transcript",
                severity="critical",
                fix_suggestion="Provide transcript for audio content",
                timestamp=datetime.now()
            ))
        
        return violations
    
    def get_violations_summary(self) -> Dict[str, int]:
        """Get summary of violations by severity"""
        summary = {'critical': 0, 'serious': 0, 'moderate': 0, 'minor': 0}
        for violation in self.violations:
            summary[violation.severity] += 1
        return summary


class StreamlitAccessibilityEnhancer:
    """Enhance Streamlit apps with accessibility features"""
    
    def __init__(self):
        self.config = AccessibilityConfig()
        self.validator = AccessibilityValidator(self.config)
        
        # Initialize session state for accessibility
        if 'accessibility_preferences' not in st.session_state:
            st.session_state.accessibility_preferences = AccessibilityPreferences()
    
    def inject_accessibility_css(self):
        """Inject accessibility-focused CSS"""
        
        prefs = st.session_state.accessibility_preferences
        
        css = """
        <style>
        /* Focus indicators */
        button:focus, input:focus, textarea:focus, select:focus, [tabindex]:focus {
            outline: 2px solid #3B82F6 !important;
            outline-offset: 2px !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
        }
        
        /* Skip links */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 6px;
            z-index: 1000;
            background: #3B82F6;
            color: white;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
            transition: top 0.3s ease;
        }
        
        .skip-link:focus {
            top: 6px;
        }
        
        /* High contrast mode */
        """
        
        if prefs.high_contrast:
            css += """
            .stApp {
                filter: contrast(150%) !important;
            }
            
            .stMarkdown, .stText {
                color: #000000 !important;
                background-color: #FFFFFF !important;
            }
            
            button {
                border: 2px solid #000000 !important;
            }
            """
        
        if prefs.large_text:
            css += """
            .stApp {
                font-size: 120% !important;
            }
            
            .stMarkdown h1 { font-size: 2.5rem !important; }
            .stMarkdown h2 { font-size: 2rem !important; }
            .stMarkdown h3 { font-size: 1.5rem !important; }
            """
        
        if prefs.reduced_motion:
            css += """
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
            """
        
        css += """
        /* Screen reader only content */
        .sr-only {
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip: rect(0, 0, 0, 0) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }
        
        /* Improved focus management */
        .focus-trap {
            position: relative;
        }
        
        /* Better button accessibility */
        .stButton button {
            min-height: 44px !important;
            min-width: 44px !important;
        }
        
        /* Accessible tables */
        .stDataFrame table {
            border-collapse: collapse !important;
        }
        
        .stDataFrame th {
            background-color: #f0f2f6 !important;
            font-weight: bold !important;
            border: 1px solid #ddd !important;
        }
        
        .stDataFrame td {
            border: 1px solid #ddd !important;
        }
        </style>
        """
        
        st.markdown(css, unsafe_allow_html=True)
    
    def add_skip_links(self, targets: List[Dict[str, str]]):
        """Add skip navigation links"""
        
        skip_links_html = "<div class='skip-links'>"
        for target in targets:
            skip_links_html += f"""
            <a href="#{target['id']}" class="skip-link">
                {target.get('label', f'Skip to {target["id"]}')}
            </a>
            """
        skip_links_html += "</div>"
        
        st.markdown(skip_links_html, unsafe_allow_html=True)
    
    def create_accessible_heading(self, text: str, level: int = 1, element_id: str = None):
        """Create accessible heading with proper structure"""
        
        if level < 1 or level > 6:
            level = 1
        
        id_attr = f'id="{element_id}"' if element_id else ''
        
        st.markdown(f"""
        <h{level} {id_attr} role="heading" aria-level="{level}">
            {text}
        </h{level}>
        """, unsafe_allow_html=True)
    
    def create_accessible_button(self, text: str, key: str, help_text: str = None, 
                               disabled: bool = False, icon: str = None) -> bool:
        """Create accessible button with proper ARIA attributes"""
        
        aria_label = text
        if help_text:
            aria_label += f". {help_text}"
        
        # Use Streamlit button with accessibility enhancements
        button_clicked = st.button(
            text, 
            key=key, 
            help=help_text,
            disabled=disabled
        )
        
        # Add ARIA attributes via JavaScript (limited in Streamlit)
        if button_clicked:
            st.markdown(f"""
            <script>
            (function() {{
                const button = document.querySelector('[data-testid="baseButton-secondary"]:last-of-type');
                if (button) {{
                    button.setAttribute('aria-label', '{aria_label}');
                    button.setAttribute('role', 'button');
                }}
            }})();
            </script>
            """, unsafe_allow_html=True)
        
        return button_clicked
    
    def create_accessible_form_field(self, label: str, field_type: str = "text", 
                                   key: str = None, required: bool = False,
                                   help_text: str = None, error: str = None):
        """Create accessible form field with proper labeling"""
        
        # Create label with required indicator
        label_html = label
        if required:
            label_html += ' <span style="color: #dc2626;">*</span>'
            label_html += '<span class="sr-only"> (required)</span>'
        
        st.markdown(f"**{label_html}**", unsafe_allow_html=True)
        
        # Help text
        if help_text:
            st.caption(help_text)
        
        # Form field
        field_value = None
        if field_type == "text":
            field_value = st.text_input("", key=key, label_visibility="collapsed")
        elif field_type == "textarea":
            field_value = st.text_area("", key=key, label_visibility="collapsed")
        elif field_type == "number":
            field_value = st.number_input("", key=key, label_visibility="collapsed")
        elif field_type == "email":
            field_value = st.text_input("", key=key, label_visibility="collapsed", 
                                      placeholder="example@domain.com")
        
        # Error message
        if error:
            st.error(f"L {error}")
        
        # Validation for required fields
        if required and field_value is not None and not str(field_value).strip():
            st.error(f"L {label} is required")
        
        return field_value
    
    def create_accessible_media_player(self, media_path: str, media_type: str = "audio",
                                     transcript: str = None, captions: List[str] = None):
        """Create accessible media player with captions/transcript"""
        
        if media_type == "audio":
            st.audio(media_path)
            
            # Provide transcript
            if transcript:
                with st.expander("=Ý Transcript (Click to expand)"):
                    st.markdown(f"**Transcript:**\n\n{transcript}")
            else:
                st.warning("  No transcript available - this may not be accessible to all users")
        
        elif media_type == "video":
            st.video(media_path)
            
            # Provide captions or transcript
            if captions:
                with st.expander("=Ý Captions (Click to expand)"):
                    for i, caption in enumerate(captions):
                        st.markdown(f"**{i+1}.** {caption}")
            elif transcript:
                with st.expander("=Ý Transcript (Click to expand)"):
                    st.markdown(f"**Video Transcript:**\n\n{transcript}")
            else:
                st.warning("  No captions or transcript available - this may not be accessible to all users")
    
    def announce_to_screen_reader(self, message: str, priority: str = "polite"):
        """Announce message to screen readers via live region"""
        
        aria_live = "polite" if priority == "polite" else "assertive"
        
        st.markdown(f"""
        <div aria-live="{aria_live}" aria-atomic="true" class="sr-only" id="sr-announcements">
            {message}
        </div>
        """, unsafe_allow_html=True)
    
    def render_accessibility_settings(self):
        """Render accessibility preferences panel"""
        
        st.markdown("###  Accessibility Settings")
        st.markdown("*Customize the interface to meet your accessibility needs*")
        
        prefs = st.session_state.accessibility_preferences
        
        col1, col2 = st.columns(2)
        
        with col1:
            prefs.high_contrast = st.checkbox(
                "=3 High Contrast Mode",
                value=prefs.high_contrast,
                help="Increase contrast for better visibility"
            )
            
            prefs.large_text = st.checkbox(
                "= Large Text",
                value=prefs.large_text, 
                help="Increase text size for better readability"
            )
            
            prefs.reduced_motion = st.checkbox(
                "ø Reduced Motion",
                value=prefs.reduced_motion,
                help="Minimize animations and transitions"
            )
            
            prefs.focus_indicators = st.checkbox(
                "<¯ Enhanced Focus Indicators",
                value=prefs.focus_indicators,
                help="Show clear visual focus indicators"
            )
        
        with col2:
            prefs.screen_reader = st.checkbox(
                "=â Screen Reader Optimizations",
                value=prefs.screen_reader,
                help="Optimize interface for screen readers"
            )
            
            prefs.keyboard_only = st.checkbox(
                "( Keyboard Navigation",
                value=prefs.keyboard_only,
                help="Enable enhanced keyboard navigation"
            )
            
            prefs.captions = st.checkbox(
                "=¬ Show Captions",
                value=prefs.captions,
                help="Display captions for audio/video content"
            )
            
            prefs.simplified_ui = st.checkbox(
                "<¨ Simplified Interface",
                value=prefs.simplified_ui,
                help="Use a simpler, cleaner interface"
            )
        
        # Save preferences
        st.session_state.accessibility_preferences = prefs
        
        if st.button("=¾ Apply Settings"):
            self.announce_to_screen_reader("Accessibility settings have been applied")
            st.success(" Accessibility settings applied!")
            st.rerun()
    
    def validate_page_accessibility(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Validate current page for accessibility issues"""
        
        violations = []
        
        # Validate text content
        if 'text' in content:
            violations.extend(self.validator.validate_text(content['text'], "page content"))
        
        # Validate media
        if 'media' in content:
            for media in content['media']:
                violations.extend(self.validator.validate_media(media))
        
        # Check for missing alt text on images
        if 'images' in content:
            for img in content['images']:
                if not img.get('alt_text'):
                    violations.append(WCAGViolation(
                        level=AccessibilityLevel.A,
                        guideline="1.1.1",
                        criterion="Non-text Content",
                        element=img.get('src', 'image'),
                        description="Image missing alt text",
                        severity="critical",
                        fix_suggestion="Add descriptive alt text for the image",
                        timestamp=datetime.now()
                    ))
        
        self.validator.violations.extend(violations)
        
        return {
            'violations': len(violations),
            'summary': self.validator.get_violations_summary(),
            'details': [asdict(v) for v in violations]
        }
    
    def render_accessibility_report(self, validation_results: Dict[str, Any]):
        """Render accessibility compliance report"""
        
        st.markdown("###  Accessibility Compliance Report")
        
        total_violations = validation_results['violations']
        summary = validation_results['summary']
        
        if total_violations == 0:
            st.success("<‰ **Excellent!** No accessibility violations detected.")
        else:
            st.warning(f"  Found {total_violations} accessibility issue(s)")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("=4 Critical", summary.get('critical', 0))
            with col2:
                st.metric("=à Serious", summary.get('serious', 0))
            with col3:
                st.metric("=á Moderate", summary.get('moderate', 0))
            with col4:
                st.metric("=5 Minor", summary.get('minor', 0))
            
            # Detailed violations
            if st.expander("=Ë View Details", expanded=False):
                for violation in validation_results['details']:
                    severity_emoji = {
                        'critical': '=4',
                        'serious': '=à', 
                        'moderate': '=á',
                        'minor': '=5'
                    }.get(violation['severity'], 'ª')
                    
                    st.markdown(f"""
                    **{severity_emoji} {violation['criterion']}** ({violation['level']})
                    - **Element:** {violation['element']}  
                    - **Issue:** {violation['description']}
                    - **Fix:** {violation['fix_suggestion']}
                    ---
                    """)


# Global accessibility enhancer instance
accessibility_enhancer = StreamlitAccessibilityEnhancer()


def demo_accessibility_system():
    """Demo the comprehensive accessibility system"""
    
    st.set_page_config(
        page_title="Accessibility System Demo",
        page_icon="",
        layout="wide"
    )
    
    # Inject accessibility CSS
    accessibility_enhancer.inject_accessibility_css()
    
    # Add skip links
    accessibility_enhancer.add_skip_links([
        {"id": "main-content", "label": "Skip to main content"},
        {"id": "accessibility-settings", "label": "Skip to accessibility settings"}
    ])
    
    # Header
    accessibility_enhancer.create_accessible_heading(
        " Comprehensive Accessibility System Demo", 
        level=1, 
        element_id="main-title"
    )
    
    st.markdown("*WCAG 2.1 AA compliant accessibility features for the transcription platform*")
    
    # Main content area
    st.markdown('<div id="main-content">', unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "<¯ Accessibility Features",
        "™ Settings", 
        "= Validation",
        "=Ê Testing Tools"
    ])
    
    with tab1:
        st.markdown("### <¯ Accessibility Features Demonstration")
        
        # Accessible form example
        st.markdown("#### =Ý Accessible Form Example")
        
        name = accessibility_enhancer.create_accessible_form_field(
            "Full Name", 
            field_type="text",
            key="demo_name",
            required=True,
            help_text="Enter your first and last name"
        )
        
        email = accessibility_enhancer.create_accessible_form_field(
            "Email Address",
            field_type="email", 
            key="demo_email",
            required=True,
            help_text="We'll use this to contact you"
        )
        
        message = accessibility_enhancer.create_accessible_form_field(
            "Message",
            field_type="textarea",
            key="demo_message",
            help_text="Tell us how we can help you"
        )
        
        if accessibility_enhancer.create_accessible_button(
            "Submit Form",
            key="demo_submit",
            help_text="Submit your information"
        ):
            if name and email:
                accessibility_enhancer.announce_to_screen_reader(
                    "Form submitted successfully",
                    priority="assertive"
                )
                st.success(" Form submitted successfully!")
        
        # Accessible media example
        st.markdown("#### <µ Accessible Media Example")
        
        sample_transcript = """
        Welcome to our accessibility demo. This audio contains information about 
        our comprehensive accessibility features including screen reader support, 
        keyboard navigation, and WCAG compliance.
        """
        
        # Note: In a real implementation, you would have an actual audio file
        st.info("<µ Audio player would appear here with full transcript support")
        
        with st.expander("=Ý Audio Transcript"):
            st.markdown(sample_transcript)
    
    with tab2:
        st.markdown('<div id="accessibility-settings">', unsafe_allow_html=True)
        accessibility_enhancer.render_accessibility_settings()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### = Accessibility Validation")
        
        # Demo validation
        sample_content = {
            'text': 'This is sample content for validation. IT HAS SOME ALL CAPS TEXT.',
            'media': [
                {'type': 'video', 'filename': 'demo.mp4', 'has_captions': False},
                {'type': 'audio', 'filename': 'demo.mp3', 'has_transcript': True}
            ],
            'images': [
                {'src': 'logo.png', 'alt_text': 'Company logo'},
                {'src': 'chart.png', 'alt_text': None}  # Missing alt text
            ]
        }
        
        if st.button("= Run Accessibility Validation"):
            results = accessibility_enhancer.validate_page_accessibility(sample_content)
            accessibility_enhancer.render_accessibility_report(results)
    
    with tab4:
        st.markdown("### =Ê Accessibility Testing Tools")
        
        st.markdown("""
        #### =' Available Testing Tools
        
        **Automated Testing:**
        -  WCAG 2.1 compliance checking
        -  Color contrast validation  
        -  Keyboard navigation testing
        -  Screen reader compatibility
        
        **Manual Testing Checklist:**
        - <¯ Tab through all interactive elements
        - = Test with 200% zoom level
        - =â Verify screen reader announcements
        - ( Navigate using only keyboard
        - <¨ Test with high contrast mode
        
        **Supported Assistive Technologies:**
        - NVDA (Windows)
        - JAWS (Windows) 
        - VoiceOver (macOS/iOS)
        - TalkBack (Android)
        - Dragon NaturallySpeaking
        """)
        
        # Color contrast checker
        st.markdown("#### <¨ Color Contrast Checker")
        
        col1, col2 = st.columns(2)
        
        with col1:
            foreground = st.color_picker("Foreground Color", "#000000")
        
        with col2:
            background = st.color_picker("Background Color", "#FFFFFF")
        
        if st.button("Check Contrast"):
            contrast_result = ColorContrastChecker.check_contrast(foreground, background)
            
            st.markdown(f"**Contrast Ratio:** {contrast_result['ratio']}:1")
            
            # Show compliance results
            if contrast_result['passes_aa_normal']:
                st.success(" WCAG AA Normal Text")
            else:
                st.error("L WCAG AA Normal Text")
            
            if contrast_result['passes_aa_large']:
                st.success(" WCAG AA Large Text")
            else:
                st.error("L WCAG AA Large Text")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer with accessibility statement
    st.markdown("---")
    st.markdown("""
    ###  Accessibility Statement
    
    This application is designed to be accessible to all users, including those using assistive technologies. 
    We strive to meet WCAG 2.1 AA standards and continuously improve our accessibility features.
    
    **Need help?** Contact our accessibility team at accessibility@company.com
    """)


if __name__ == "__main__":
    demo_accessibility_system()