"""
Third-Party Ecosystem Demo
Demonstrates comprehensive integration capabilities with external APIs, plugins, webhooks, and automation
"""

import asyncio
import json
import time
from datetime import datetime
from third_party_ecosystem import ThirdPartyEcosystem, IntegrationHelpers

async def main():
    """Main demo function"""
    print("🔗 THIRD-PARTY ECOSYSTEM DEMO")
    print("=" * 70)
    print("This demo showcases comprehensive integration capabilities including:")
    print("• Plugin architecture for custom integrations")
    print("• Webhook marketplace for automated workflows")
    print("• External API integrations (OpenAI, HuggingFace, CRMs)")
    print("• Zapier/IFTTT automation support")
    print("• Browser extension capabilities")
    print("• Native CRM integrations")
    print()
    
    # Initialize ecosystem
    ecosystem = ThirdPartyEcosystem()
    
    # Demo sections
    await demo_external_apis(ecosystem)
    await demo_plugin_system(ecosystem)
    await demo_webhook_system(ecosystem)
    await demo_crm_integrations(ecosystem)
    await demo_automation_features(ecosystem)
    await demo_browser_extension(ecosystem)
    await demo_marketplace(ecosystem)
    await demo_analytics(ecosystem)
    
    print("\n🎉 Demo completed successfully!")
    print("The third-party ecosystem provides comprehensive integration capabilities")
    print("for connecting with external services, automating workflows, and extending functionality.")

async def demo_external_apis(ecosystem):
    """Demo external API integrations"""
    print("\n" + "=" * 70)
    print("  🌐 EXTERNAL API INTEGRATIONS")
    print("=" * 70)
    
    print("\n--- Available External APIs ---")
    api_count = 0
    for api_name, api_config in ecosystem.external_apis.items():
        api_count += 1
        status = "✅ Configured" if api_config.api_key else "❌ Not Configured"
        print(f"{api_count:2d}. {api_config.name:<20} - {status}")
        print(f"    Base URL: {api_config.base_url}")
        print(f"    Auth Type: {api_config.auth_type}")
        print(f"    Rate Limit: {api_config.rate_limit} requests/hour")
        
        if api_config.models:
            models_display = ", ".join(api_config.models[:3])
            if len(api_config.models) > 3:
                models_display += f" (+{len(api_config.models) - 3} more)"
            print(f"    Models: {models_display}")
        
        if api_config.capabilities:
            capabilities_display = ", ".join(api_config.capabilities[:3])
            if len(api_config.capabilities) > 3:
                capabilities_display += f" (+{len(api_config.capabilities) - 3} more)"
            print(f"    Capabilities: {capabilities_display}")
        print()
    
    print(f"✅ Total External APIs Configured: {api_count}")
    
    # Demo API categories
    print("\n--- API Categories ---")
    categories = {
        "AI/ML APIs": ["openai", "anthropic", "huggingface", "cohere"],
        "Speech/Audio APIs": ["elevenlabs", "assemblyai"],
        "CRM APIs": ["salesforce", "hubspot"],
        "Communication APIs": ["slack", "discord"],
        "Cloud Storage APIs": ["google_drive", "dropbox"],
        "Project Management APIs": ["jira", "asana", "trello"],
        "Video/Media APIs": ["youtube", "zoom"],
        "Translation APIs": ["google_translate", "deepl"]
    }
    
    for category, apis in categories.items():
        configured_count = sum(1 for api in apis if ecosystem.external_apis.get(api, {}).api_key)
        total_count = len(apis)
        print(f"{category:<25} {configured_count}/{total_count} configured")
    
    # Simulate API calls
    print("\n--- Simulating API Calls ---")
    
    # OpenAI API simulation
    print("🤖 Testing OpenAI GPT-4 integration...")
    try:
        # Simulate API call
        await asyncio.sleep(0.5)
        print("   ✅ GPT-4 text generation: Success")
        print("   📊 Response time: 180ms")
        print("   💰 Tokens used: 150")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # HuggingFace API simulation
    print("\n🤗 Testing HuggingFace model integration...")
    try:
        await asyncio.sleep(0.3)
        print("   ✅ BART summarization model: Success")
        print("   📊 Response time: 250ms")
        print("   🎯 Model: facebook/bart-large-cnn")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # ElevenLabs API simulation
    print("\n🎵 Testing ElevenLabs TTS integration...")
    try:
        await asyncio.sleep(0.4)
        print("   ✅ Voice synthesis: Success")
        print("   📊 Response time: 320ms")
        print("   🎤 Voice: Professional Female")
    except Exception as e:
        print(f"   ❌ Error: {e}")

async def demo_plugin_system(ecosystem):
    """Demo plugin architecture"""
    print("\n" + "=" * 70)
    print("  🔌 PLUGIN ARCHITECTURE")
    print("=" * 70)
    
    print("\n--- Installing Sample Plugins ---")
    
    # Sample plugin configurations
    plugins = [
        {
            'name': 'Advanced PDF Processor',
            'version': '2.1.0',
            'description': 'Extract text, images, and metadata from PDF files',
            'author': 'AI Tools Inc.',
            'category': 'document',
            'capabilities': ['text_extraction', 'image_extraction', 'metadata_parsing']
        },
        {
            'name': 'Video Content Analyzer',
            'version': '1.5.0',
            'description': 'Analyze video content for objects, scenes, and activities',
            'author': 'VisionTech',
            'category': 'media',
            'capabilities': ['object_detection', 'scene_analysis', 'activity_recognition']
        },
        {
            'name': 'Multi-Language Translator',
            'version': '3.0.0',
            'description': 'Translate content between 100+ languages',
            'author': 'LangBridge',
            'category': 'nlp',
            'capabilities': ['translation', 'language_detection', 'transliteration']
        },
        {
            'name': 'Audio Enhancement Suite',
            'version': '1.8.0',
            'description': 'Enhance audio quality with noise reduction and normalization',
            'author': 'AudioPro',
            'category': 'audio',
            'capabilities': ['noise_reduction', 'volume_normalization', 'quality_enhancement']
        }
    ]
    
    installed_plugins = []
    
    for plugin in plugins:
        print(f"📦 Installing {plugin['name']} v{plugin['version']}...")
        try:
            # Simulate plugin installation
            plugin_id = ecosystem.install_plugin("dummy_path", plugin)
            installed_plugins.append(plugin_id)
            
            print(f"   ✅ Installed successfully (ID: {plugin_id})")
            print(f"   📝 Description: {plugin['description']}")
            print(f"   👤 Author: {plugin['author']}")
            print(f"   🏷️ Category: {plugin['category']}")
            print(f"   ⚡ Capabilities: {', '.join(plugin['capabilities'])}")
            
            # Activate plugin
            if ecosystem.activate_plugin(plugin_id):
                print(f"   🟢 Plugin activated")
            
        except Exception as e:
            print(f"   ❌ Installation failed: {e}")
        
        print()
    
    print(f"✅ Successfully installed {len(installed_plugins)} plugins")
    
    # Demo plugin execution
    print("\n--- Plugin Execution Demo ---")
    
    for i, plugin_id in enumerate(installed_plugins[:2]):  # Demo first 2 plugins
        plugin_name = plugins[i]['name']
        print(f"🚀 Executing {plugin_name}...")
        
        try:
            # Simulate plugin execution
            result = ecosystem.execute_plugin(
                plugin_id, 
                "process", 
                input_data="sample_input.pdf",
                options={"quality": "high", "extract_images": True}
            )
            
            print(f"   ✅ Execution successful")
            print(f"   📊 Result: {result[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Execution failed: {e}")
        
        print()

async def demo_webhook_system(ecosystem):
    """Demo webhook marketplace"""
    print("\n" + "=" * 70)
    print("  🪝 WEBHOOK MARKETPLACE")
    print("=" * 70)
    
    print("\n--- Registering Webhooks ---")
    
    # Sample webhook configurations
    webhooks = [
        {
            'name': 'Slack Transcription Notifications',
            'url': 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX',
            'events': ['transcription.completed', 'transcription.failed'],
            'description': 'Send notifications to Slack when transcription is completed or fails'
        },
        {
            'name': 'Discord Analysis Updates',
            'url': 'https://discord.com/api/webhooks/123456789/abcdefghijklmnopqrstuvwxyz',
            'events': ['analysis.finished', 'insights.generated'],
            'description': 'Post analysis results and insights to Discord channel'
        },
        {
            'name': 'Custom API Integration',
            'url': 'https://api.example.com/webhooks/media-processor',
            'events': ['file.uploaded', 'processing.started', 'processing.completed'],
            'description': 'Integrate with custom API for workflow automation'
        },
        {
            'name': 'CRM Lead Updates',
            'url': 'https://api.mycrm.com/webhooks/leads',
            'events': ['contact.extracted', 'lead.identified'],
            'description': 'Update CRM system when new contacts or leads are identified'
        }
    ]
    
    registered_webhooks = []
    
    for webhook in webhooks:
        print(f"🔗 Registering {webhook['name']}...")
        try:
            webhook_id = ecosystem.register_webhook(
                name=webhook['name'],
                url=webhook['url'],
                events=webhook['events'],
                secret="webhook_secret_key"
            )
            
            registered_webhooks.append(webhook_id)
            
            print(f"   ✅ Registered successfully (ID: {webhook_id})")
            print(f"   📝 Description: {webhook['description']}")
            print(f"   🎯 Events: {', '.join(webhook['events'])}")
            print(f"   🔒 Security: HMAC-SHA256 signature")
            
        except Exception as e:
            print(f"   ❌ Registration failed: {e}")
        
        print()
    
    print(f"✅ Successfully registered {len(registered_webhooks)} webhooks")
    
    # Demo webhook triggering
    print("\n--- Webhook Triggering Demo ---")
    
    sample_events = [
        {
            'event': 'transcription.completed',
            'data': {
                'file_id': 'audio_123.mp3',
                'duration': 180,
                'transcript': 'This is a sample transcription...',
                'confidence': 0.95,
                'language': 'en-US'
            }
        },
        {
            'event': 'analysis.finished',
            'data': {
                'file_id': 'video_456.mp4',
                'entities': ['John Doe', 'Acme Corp', 'New York'],
                'sentiment': 'positive',
                'topics': ['business', 'technology', 'innovation']
            }
        }
    ]
    
    for event_data in sample_events:
        print(f"📡 Triggering webhooks for event: {event_data['event']}")
        
        try:
            await ecosystem.trigger_webhooks(event_data['event'], event_data['data'])
            print(f"   ✅ Webhooks triggered successfully")
            print(f"   📊 Event data: {json.dumps(event_data['data'], indent=2)[:100]}...")
            
        except Exception as e:
            print(f"   ❌ Webhook triggering failed: {e}")
        
        print()

async def demo_crm_integrations(ecosystem):
    """Demo CRM integrations"""
    print("\n" + "=" * 70)
    print("  🏢 CRM INTEGRATIONS")
    print("=" * 70)
    
    print("\n--- Salesforce Integration Demo ---")
    
    # Sample lead data
    lead_data = {
        'FirstName': 'John',
        'LastName': 'Doe',
        'Email': 'john.doe@example.com',
        'Company': 'Acme Corporation',
        'Phone': '+1-555-123-4567',
        'LeadSource': 'AI Media Processor',
        'Status': 'New',
        'Description': 'Lead identified from transcription analysis'
    }
    
    print("👤 Creating Salesforce lead...")
    try:
        # Simulate Salesforce API call
        await asyncio.sleep(0.5)
        result = await ecosystem.sync_with_salesforce('create_lead', lead_data)
        print("   ✅ Lead created successfully")
        print(f"   🆔 Lead ID: SF_LEAD_12345")
        print(f"   📧 Email: {lead_data['Email']}")
        print(f"   🏢 Company: {lead_data['Company']}")
        
    except Exception as e:
        print(f"   ❌ Salesforce sync failed: {e}")
    
    print("\n--- HubSpot Integration Demo ---")
    
    # Sample contact data
    contact_data = {
        'firstname': 'Jane',
        'lastname': 'Smith',
        'email': 'jane.smith@techcorp.com',
        'company': 'TechCorp Inc.',
        'phone': '+1-555-987-6543',
        'lifecyclestage': 'lead',
        'hs_lead_status': 'NEW'
    }
    
    print("👤 Creating HubSpot contact...")
    try:
        # Simulate HubSpot API call
        await asyncio.sleep(0.4)
        result = await ecosystem.sync_with_hubspot('create_contact', contact_data)
        print("   ✅ Contact created successfully")
        print(f"   🆔 Contact ID: HS_CONTACT_67890")
        print(f"   📧 Email: {contact_data['email']}")
        print(f"   🏢 Company: {contact_data['company']}")
        
    except Exception as e:
        print(f"   ❌ HubSpot sync failed: {e}")
    
    # Sample deal data
    deal_data = {
        'dealname': 'AI Media Processing Contract',
        'amount': '50000',
        'dealstage': 'qualifiedtobuy',
        'pipeline': 'default',
        'closedate': '2024-03-15'
    }
    
    print("\n💼 Creating HubSpot deal...")
    try:
        await asyncio.sleep(0.3)
        result = await ecosystem.sync_with_hubspot('create_deal', deal_data)
        print("   ✅ Deal created successfully")
        print(f"   🆔 Deal ID: HS_DEAL_11111")
        print(f"   💰 Amount: ${deal_data['amount']}")
        print(f"   📅 Close Date: {deal_data['closedate']}")
        
    except Exception as e:
        print(f"   ❌ HubSpot deal creation failed: {e}")

async def demo_automation_features(ecosystem):
    """Demo automation features (Zapier/IFTTT)"""
    print("\n" + "=" * 70)
    print("  ⚡ AUTOMATION FEATURES")
    print("=" * 70)
    
    print("\n--- Zapier Integration ---")
    
    # Demo Zapier triggers
    zapier_triggers = [
        {
            'name': 'new_transcription',
            'description': 'Triggers when a new transcription is completed',
            'sample_data': {
                'id': 'trans_123',
                'file_name': 'meeting_recording.mp3',
                'transcript': 'This is the transcribed content...',
                'duration': 1800,
                'language': 'en-US',
                'confidence': 0.95
            }
        },
        {
            'name': 'analysis_complete',
            'description': 'Triggers when AI analysis is finished',
            'sample_data': {
                'id': 'analysis_456',
                'file_name': 'presentation.mp4',
                'entities': ['John Smith', 'Acme Corp', 'Q4 Results'],
                'sentiment': 'positive',
                'topics': ['business', 'finance', 'growth'],
                'summary': 'Quarterly results presentation showing strong growth...'
            }
        }
    ]
    
    print("🔗 Creating Zapier triggers...")
    for trigger in zapier_triggers:
        print(f"   📡 {trigger['name']}: {trigger['description']}")
        
        # Create Zapier trigger configuration
        trigger_config = ecosystem.create_zapier_trigger(
            trigger['name'],
            trigger['description'],
            trigger['sample_data']
        )
        
        print(f"      ✅ Trigger configured")
        print(f"      🔗 Webhook URL: /api/zapier/triggers/{trigger['name']}")
    
    # Demo Zapier actions
    zapier_actions = [
        {
            'name': 'start_transcription',
            'description': 'Start transcribing an audio or video file',
            'input_fields': [
                {'key': 'file_url', 'label': 'File URL', 'type': 'string', 'required': True},
                {'key': 'language', 'label': 'Language', 'type': 'string', 'default': 'auto'},
                {'key': 'format', 'label': 'Output Format', 'type': 'string', 'choices': ['text', 'srt', 'vtt']}
            ]
        },
        {
            'name': 'get_analysis',
            'description': 'Get AI analysis results for a processed file',
            'input_fields': [
                {'key': 'file_id', 'label': 'File ID', 'type': 'string', 'required': True},
                {'key': 'analysis_type', 'label': 'Analysis Type', 'type': 'string', 'choices': ['entities', 'sentiment', 'summary', 'all']}
            ]
        }
    ]
    
    print("\n⚡ Creating Zapier actions...")
    for action in zapier_actions:
        print(f"   🎯 {action['name']}: {action['description']}")
        
        # Create Zapier action configuration
        action_config = ecosystem.create_zapier_action(
            action['name'],
            action['description'],
            action['input_fields']
        )
        
        print(f"      ✅ Action configured")
        print(f"      🔗 Endpoint: /api/zapier/actions/{action['name']}")
    
    print("\n--- IFTTT Integration ---")
    
    # Demo IFTTT applets
    ifttt_applets = [
        {
            'trigger': 'New file uploaded',
            'action': 'Send email notification',
            'description': 'Get notified via email when a new file is uploaded for processing'
        },
        {
            'trigger': 'Transcription completed',
            'action': 'Save to Google Drive',
            'description': 'Automatically save transcription results to Google Drive'
        },
        {
            'trigger': 'Error occurred',
            'action': 'Send SMS alert',
            'description': 'Get SMS alerts when processing errors occur'
        },
        {
            'trigger': 'Analysis finished',
            'action': 'Post to Slack',
            'description': 'Share analysis results in Slack channel'
        }
    ]
    
    print("🔗 Available IFTTT applets:")
    for i, applet in enumerate(ifttt_applets, 1):
        print(f"   {i}. If {applet['trigger']} → Then {applet['action']}")
        print(f"      📝 {applet['description']}")
    
    print("\n--- Custom Workflow Demo ---")
    
    # Demo custom workflow
    workflow = {
        'name': 'Meeting Processing Workflow',
        'trigger': 'File Upload',
        'conditions': [
            {'field': 'file_type', 'operator': 'equals', 'value': 'audio'},
            {'field': 'duration', 'operator': 'greater_than', 'value': 300}  # 5 minutes
        ],
        'actions': [
            {'type': 'transcribe', 'params': {'language': 'auto', 'speaker_diarization': True}},
            {'type': 'analyze', 'params': {'extract_entities': True, 'sentiment_analysis': True}},
            {'type': 'generate_summary', 'params': {'max_length': 200}},
            {'type': 'send_email', 'params': {'template': 'meeting_summary', 'recipients': ['team@company.com']}},
            {'type': 'update_crm', 'params': {'system': 'salesforce', 'create_tasks': True}}
        ]
    }
    
    print(f"🔄 Custom Workflow: {workflow['name']}")
    print(f"   🎯 Trigger: {workflow['trigger']}")
    print(f"   ⚖️ Conditions: {len(workflow['conditions'])} conditions")
    print(f"   ⚡ Actions: {len(workflow['actions'])} actions")
    
    for i, action in enumerate(workflow['actions'], 1):
        print(f"      {i}. {action['type']}")
    
    print("   ✅ Workflow configured and ready")

async def demo_browser_extension(ecosystem):
    """Demo browser extension capabilities"""
    print("\n" + "=" * 70)
    print("  🌐 BROWSER EXTENSION")
    print("=" * 70)
    
    print("\n--- Extension Capabilities ---")
    
    capabilities = [
        {
            'name': 'Video Capture',
            'description': 'Capture and transcribe videos from any website',
            'supported_sites': ['YouTube', 'Vimeo', 'Wistia', 'Custom video players']
        },
        {
            'name': 'Audio Extraction',
            'description': 'Extract audio from web media for processing',
            'supported_formats': ['MP3', 'WAV', 'M4A', 'WebM Audio']
        },
        {
            'name': 'Text Extraction',
            'description': 'Extract text from images and documents on web pages',
            'supported_types': ['Images (OCR)', 'PDF files', 'Document viewers']
        },
        {
            'name': 'Content Analysis',
            'description': 'Analyze web content with AI',
            'features': ['Entity extraction', 'Sentiment analysis', 'Summarization']
        },
        {
            'name': 'Auto Save',
            'description': 'Automatically save results to your account',
            'options': ['Cloud storage', 'Local download', 'Email delivery']
        }
    ]
    
    for i, capability in enumerate(capabilities, 1):
        print(f"{i}. 🎯 {capability['name']}")
        print(f"   📝 {capability['description']}")
        
        if 'supported_sites' in capability:
            print(f"   🌐 Supported sites: {', '.join(capability['supported_sites'])}")
        elif 'supported_formats' in capability:
            print(f"   📁 Supported formats: {', '.join(capability['supported_formats'])}")
        elif 'supported_types' in capability:
            print(f"   📄 Supported types: {', '.join(capability['supported_types'])}")
        elif 'features' in capability:
            print(f"   ⚡ Features: {', '.join(capability['features'])}")
        elif 'options' in capability:
            print(f"   ⚙️ Options: {', '.join(capability['options'])}")
        
        print()
    
    print("--- Extension Manifest Generation ---")
    
    # Generate browser extension manifest
    manifest = ecosystem.generate_browser_extension_manifest("AI Media Processor")
    
    print("📄 Generated browser extension manifest:")
    print(f"   📛 Name: {manifest['name']}")
    print(f"   🔢 Version: {manifest['version']}")
    print(f"   📝 Description: {manifest['description']}")
    print(f"   🔒 Permissions: {len(manifest['permissions'])} permissions")
    print(f"   🌐 Host Permissions: {len(manifest['host_permissions'])} host patterns")
    print(f"   📜 Content Scripts: {len(manifest['content_scripts'])} scripts")
    
    print("\n--- Installation Statistics ---")
    
    # Simulated installation stats
    stats = {
        'Chrome Web Store': {'downloads': 15420, 'rating': 4.8, 'reviews': 342},
        'Firefox Add-ons': {'downloads': 8930, 'rating': 4.7, 'reviews': 189},
        'Edge Add-ons': {'downloads': 3210, 'rating': 4.9, 'reviews': 87}
    }
    
    total_downloads = sum(store['downloads'] for store in stats.values())
    avg_rating = sum(store['rating'] for store in stats.values()) / len(stats)
    total_reviews = sum(store['reviews'] for store in stats.values())
    
    print(f"📊 Total Downloads: {total_downloads:,}")
    print(f"⭐ Average Rating: {avg_rating:.1f}/5.0")
    print(f"💬 Total Reviews: {total_reviews}")
    
    print("\n📈 Store-specific statistics:")
    for store, data in stats.items():
        print(f"   {store}:")
        print(f"      Downloads: {data['downloads']:,}")
        print(f"      Rating: {data['rating']}/5.0")
        print(f"      Reviews: {data['reviews']}")

async def demo_marketplace(ecosystem):
    """Demo integration marketplace"""
    print("\n" + "=" * 70)
    print("  🏪 INTEGRATION MARKETPLACE")
    print("=" * 70)
    
    print("\n--- Featured Integrations ---")
    
    featured_integrations = [
        {
            'name': 'Advanced AI Analysis Pro',
            'description': 'Enhanced AI analysis with GPT-4, Claude, and custom models',
            'category': 'AI/ML',
            'author': 'AI Innovations Inc.',
            'version': '2.5.0',
            'price': 49.99,
            'rating': 4.9,
            'downloads': 8420,
            'features': ['Multi-model analysis', 'Custom fine-tuning', 'Batch processing', 'API access']
        },
        {
            'name': 'Enterprise CRM Sync',
            'description': 'Advanced CRM integration with Salesforce, HubSpot, and Pipedrive',
            'category': 'CRM',
            'author': 'CRM Solutions Ltd.',
            'version': '3.1.0',
            'price': 29.99,
            'rating': 4.8,
            'downloads': 5630,
            'features': ['Real-time sync', 'Custom field mapping', 'Bulk operations', 'Workflow automation']
        },
        {
            'name': 'Communication Hub',
            'description': 'Integrate with Slack, Discord, Teams, and 50+ messaging platforms',
            'category': 'Communication',
            'author': 'ConnectTech',
            'version': '1.8.0',
            'price': 19.99,
            'rating': 4.7,
            'downloads': 12100,
            'features': ['Multi-platform support', 'Rich notifications', 'File sharing', 'Bot integration']
        }
    ]
    
    for i, integration in enumerate(featured_integrations, 1):
        print(f"⭐ {i}. {integration['name']} v{integration['version']}")
        print(f"   📝 {integration['description']}")
        print(f"   👤 Author: {integration['author']}")
        print(f"   🏷️ Category: {integration['category']}")
        print(f"   💰 Price: ${integration['price']}")
        print(f"   ⭐ Rating: {integration['rating']}/5.0 ({integration['downloads']:,} downloads)")
        print(f"   ⚡ Features: {', '.join(integration['features'])}")
        print()
    
    print("--- Marketplace Statistics ---")
    
    # Marketplace stats
    marketplace_stats = {
        'total_integrations': 247,
        'free_integrations': 156,
        'paid_integrations': 91,
        'categories': {
            'AI/ML': 45,
            'CRM': 32,
            'Communication': 38,
            'Storage': 28,
            'Analytics': 24,
            'Automation': 35,
            'Media': 22,
            'Other': 23
        },
        'total_downloads': 156420,
        'active_developers': 89,
        'avg_rating': 4.6
    }
    
    print(f"📊 Total Integrations: {marketplace_stats['total_integrations']}")
    print(f"🆓 Free: {marketplace_stats['free_integrations']} | 💰 Paid: {marketplace_stats['paid_integrations']}")
    print(f"📥 Total Downloads: {marketplace_stats['total_downloads']:,}")
    print(f"👨‍💻 Active Developers: {marketplace_stats['active_developers']}")
    print(f"⭐ Average Rating: {marketplace_stats['avg_rating']}/5.0")
    
    print("\n📂 Categories:")
    for category, count in marketplace_stats['categories'].items():
        print(f"   {category}: {count} integrations")
    
    # Search demo
    print("\n--- Search Demo ---")
    
    search_queries = ['AI analysis', 'Slack integration', 'PDF processing', 'video transcription']
    
    for query in search_queries:
        print(f"🔍 Searching for: '{query}'")
        
        # Simulate search
        results = ecosystem.search_marketplace(query)
        print(f"   📊 Found {len(results)} results")
        
        # Show sample results
        if results:
            for result in results[:2]:  # Show first 2 results
                print(f"      • {result.get('name', 'Unknown')} - {result.get('description', 'No description')[:50]}...")
        
        print()

async def demo_analytics(ecosystem):
    """Demo integration analytics"""
    print("\n" + "=" * 70)
    print("  📊 INTEGRATION ANALYTICS")
    print("=" * 70)
    
    # Get analytics data
    analytics = ecosystem.get_integration_analytics()
    
    print("\n--- System Overview ---")
    print(f"🔌 Active Plugins: {analytics.get('total_plugins', 0)}")
    print(f"🪝 Active Webhooks: {analytics.get('total_webhooks', 0)}")
    print(f"🌐 External APIs: {analytics.get('total_apis', 0)}")
    
    # Usage statistics
    print("\n--- Usage Statistics ---")
    
    usage_stats = {
        'total_api_calls': 45620,
        'successful_calls': 44980,
        'failed_calls': 640,
        'avg_response_time': 245,
        'peak_usage_hour': '14:00-15:00',
        'most_used_api': 'OpenAI GPT-4',
        'success_rate': 98.6
    }
    
    print(f"📞 Total API Calls: {usage_stats['total_api_calls']:,}")
    print(f"✅ Successful: {usage_stats['successful_calls']:,} ({usage_stats['success_rate']:.1f}%)")
    print(f"❌ Failed: {usage_stats['failed_calls']:,}")
    print(f"⏱️ Avg Response Time: {usage_stats['avg_response_time']}ms")
    print(f"📈 Peak Usage: {usage_stats['peak_usage_hour']}")
    print(f"🏆 Most Used API: {usage_stats['most_used_api']}")
    
    # Top performing integrations
    print("\n--- Top Performing Integrations ---")
    
    top_integrations = [
        {'name': 'OpenAI GPT-4', 'calls': 18420, 'success_rate': 99.2, 'avg_time': 180},
        {'name': 'HuggingFace BART', 'calls': 12350, 'success_rate': 98.8, 'avg_time': 250},
        {'name': 'ElevenLabs TTS', 'calls': 8930, 'success_rate': 99.5, 'avg_time': 320},
        {'name': 'Slack Webhooks', 'calls': 5640, 'success_rate': 97.8, 'avg_time': 95},
        {'name': 'Salesforce CRM', 'calls': 3210, 'success_rate': 96.5, 'avg_time': 380}
    ]
    
    for i, integration in enumerate(top_integrations, 1):
        print(f"{i}. {integration['name']}")
        print(f"   📞 Calls: {integration['calls']:,}")
        print(f"   ✅ Success Rate: {integration['success_rate']:.1f}%")
        print(f"   ⏱️ Avg Time: {integration['avg_time']}ms")
    
    # Error analysis
    print("\n--- Error Analysis ---")
    
    error_breakdown = {
        'Timeout': 35,
        'Authentication': 25,
        'Rate Limit': 20,
        'Server Error': 15,
        'Network': 5
    }
    
    total_errors = sum(error_breakdown.values())
    
    print(f"🚨 Total Errors: {total_errors}")
    print("📊 Error Breakdown:")
    
    for error_type, count in error_breakdown.items():
        percentage = (count / total_errors) * 100
        print(f"   {error_type}: {count} ({percentage:.1f}%)")
    
    # Performance trends
    print("\n--- Performance Trends ---")
    
    trends = {
        'api_calls_growth': '+12.5%',
        'success_rate_change': '+0.8%',
        'response_time_change': '-15ms',
        'new_integrations': 8,
        'integration_updates': 23
    }
    
    print(f"📈 API Calls Growth: {trends['api_calls_growth']} (last 30 days)")
    print(f"✅ Success Rate Change: {trends['success_rate_change']} (last 30 days)")
    print(f"⚡ Response Time Improvement: {trends['response_time_change']} (last 30 days)")
    print(f"🆕 New Integrations: {trends['new_integrations']} (this month)")
    print(f"🔄 Integration Updates: {trends['integration_updates']} (this month)")
    
    # Cost analysis
    print("\n--- Cost Analysis ---")
    
    cost_breakdown = {
        'OpenAI API': 1250.50,
        'HuggingFace Pro': 89.99,
        'ElevenLabs': 299.00,
        'Cloud Storage': 45.20,
        'Other APIs': 156.80
    }
    
    total_cost = sum(cost_breakdown.values())
    
    print(f"💰 Total Monthly Cost: ${total_cost:.2f}")
    print("📊 Cost Breakdown:")
    
    for service, cost in cost_breakdown.items():
        percentage = (cost / total_cost) * 100
        print(f"   {service}: ${cost:.2f} ({percentage:.1f}%)")
    
    # Recommendations
    print("\n--- Optimization Recommendations ---")
    
    recommendations = [
        "🔧 Consider implementing caching for OpenAI API calls to reduce costs by ~20%",
        "⚡ Optimize webhook retry logic to improve success rates",
        "📊 Monitor rate limits more closely during peak hours (14:00-15:00)",
        "🔄 Update authentication tokens for Salesforce integration",
        "💡 Consider upgrading to HuggingFace Enterprise for better performance"
    ]
    
    for i, recommendation in enumerate(recommendations, 1):
        print(f"{i}. {recommendation}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🧹 Demo cleanup completed")