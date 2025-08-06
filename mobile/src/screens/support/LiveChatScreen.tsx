import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Keyboard,
  Alert
} from 'react-native';
import {
  Header,
  Icon,
  Avatar,
  Badge,
  ListItem,
  Chip,
  Card,
  Button,
  Overlay
} from 'react-native-elements';
import { useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as DocumentPicker from 'expo-document-picker';
import * as ImagePicker from 'expo-image-picker';

interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'assistant' | 'system';
  timestamp: Date;
  attachments?: Array<{
    name: string;
    type: string;
    uri: string;
  }>;
  suggestedArticles?: Array<{
    title: string;
    id: string;
  }>;
}

export default function LiveChatScreen() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [attachments, setAttachments] = useState<any[]>([]);
  const [showOptions, setShowOptions] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);
  const navigation = useNavigation();

  useEffect(() => {
    initializeChat();
  }, []);

  const initializeChat = async () => {
    // Initialize chat session
    const newSessionId = `chat_${Date.now()}`;
    setSessionId(newSessionId);
    
    // Add welcome message
    setMessages([
      {
        id: '1',
        text: "Hello! I'm your support assistant. How can I help you today?",
        sender: 'assistant',
        timestamp: new Date(),
        suggestedArticles: [
          { title: 'Getting Started Guide', id: 'article_1' },
          { title: 'Common Issues & Solutions', id: 'article_2' }
        ]
      }
    ]);
  };

  const sendMessage = async () => {
    if (!inputText.trim() && attachments.length === 0) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
      attachments: attachments
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setAttachments([]);
    setIsTyping(true);
    
    // Simulate AI response
    setTimeout(() => {
      const responses = [
        {
          text: "I understand your concern. Let me help you with that.",
          suggestedArticles: []
        },
        {
          text: "I can see you're having trouble with transcription. Have you tried checking your audio file format?",
          suggestedArticles: [
            { title: 'Supported Audio Formats', id: 'article_3' },
            { title: 'Troubleshooting Guide', id: 'article_4' }
          ]
        },
        {
          text: "For billing questions, I can help you understand your current plan and charges.",
          suggestedArticles: [
            { title: 'Billing FAQ', id: 'article_5' }
          ]
        }
      ];

      const response = responses[Math.floor(Math.random() * responses.length)];
      
      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now()}_assistant`,
        text: response.text,
        sender: 'assistant',
        timestamp: new Date(),
        suggestedArticles: response.suggestedArticles
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 1500);

    // Scroll to bottom
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const handleAttachment = async (type: 'photo' | 'document') => {
    if (type === 'photo') {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 1,
      });

      if (!result.canceled) {
        setAttachments([...attachments, {
          name: 'image.jpg',
          type: 'image',
          uri: result.assets[0].uri
        }]);
      }
    } else {
      const result = await DocumentPicker.getDocumentAsync({
        type: '*/*',
        copyToCacheDirectory: true
      });

      if (result.type === 'success') {
        setAttachments([...attachments, {
          name: result.name,
          type: 'document',
          uri: result.uri
        }]);
      }
    }
    setShowOptions(false);
  };

  const escalateToHuman = () => {
    Alert.alert(
      'Connect to Human Agent',
      'Would you like to create a support ticket for human assistance?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Create Ticket',
          onPress: () => navigation.navigate('CreateTicket' as any)
        }
      ]
    );
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.sender === 'user';
    
    return (
      <View
        key={message.id}
        style={[
          styles.messageContainer,
          isUser ? styles.userMessageContainer : styles.assistantMessageContainer
        ]}
      >
        {!isUser && (
          <Avatar
            rounded
            source={{ uri: 'https://ui-avatars.com/api/?name=Support&background=2196F3&color=fff' }}
            size="small"
            containerStyle={styles.avatar}
          />
        )}
        
        <View
          style={[
            styles.messageBubble,
            isUser ? styles.userBubble : styles.assistantBubble
          ]}
        >
          <Text style={[styles.messageText, isUser && styles.userMessageText]}>
            {message.text}
          </Text>
          
          {message.attachments && message.attachments.length > 0 && (
            <View style={styles.attachmentsContainer}>
              {message.attachments.map((attachment, index) => (
                <Chip
                  key={index}
                  title={attachment.name}
                  icon={{
                    name: attachment.type === 'image' ? 'image' : 'attach-file',
                    color: isUser ? '#fff' : '#666'
                  }}
                  buttonStyle={[
                    styles.attachmentChip,
                    isUser && styles.userAttachmentChip
                  ]}
                  titleStyle={isUser ? styles.userChipTitle : styles.chipTitle}
                />
              ))}
            </View>
          )}
          
          {message.suggestedArticles && message.suggestedArticles.length > 0 && (
            <Card containerStyle={styles.suggestedArticlesCard}>
              <Text style={styles.suggestedTitle}>Related Articles:</Text>
              {message.suggestedArticles.map((article, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.articleLink}
                  onPress={() => navigation.navigate('ArticleDetail', { articleId: article.id } as any)}
                >
                  <Icon name="article" size={16} color="#2196F3" />
                  <Text style={styles.articleTitle}>{article.title}</Text>
                </TouchableOpacity>
              ))}
            </Card>
          )}
          
          <Text style={[styles.timestamp, isUser && styles.userTimestamp]}>
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Text>
        </View>
        
        {isUser && (
          <Avatar
            rounded
            source={{ uri: 'https://ui-avatars.com/api/?name=You&background=4CAF50&color=fff' }}
            size="small"
            containerStyle={styles.avatar}
          />
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <Header
        leftComponent={
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Icon name="arrow-back" color="#fff" />
          </TouchableOpacity>
        }
        centerComponent={
          <View style={styles.headerCenter}>
            <Text style={styles.headerTitle}>Support Chat</Text>
            <View style={styles.statusContainer}>
              <View style={styles.statusDot} />
              <Text style={styles.statusText}>Online</Text>
            </View>
          </View>
        }
        rightComponent={
          <TouchableOpacity onPress={escalateToHuman}>
            <Icon name="person" color="#fff" />
          </TouchableOpacity>
        }
        backgroundColor="#2196F3"
      />

      <KeyboardAvoidingView
        style={styles.chatContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      >
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
        >
          {messages.map(renderMessage)}
          
          {isTyping && (
            <View style={[styles.messageContainer, styles.assistantMessageContainer]}>
              <Avatar
                rounded
                source={{ uri: 'https://ui-avatars.com/api/?name=Support&background=2196F3&color=fff' }}
                size="small"
                containerStyle={styles.avatar}
              />
              <View style={[styles.messageBubble, styles.assistantBubble, styles.typingBubble]}>
                <View style={styles.typingIndicator}>
                  <View style={[styles.typingDot, { animationDelay: '0ms' }]} />
                  <View style={[styles.typingDot, { animationDelay: '200ms' }]} />
                  <View style={[styles.typingDot, { animationDelay: '400ms' }]} />
                </View>
              </View>
            </View>
          )}
        </ScrollView>

        {attachments.length > 0 && (
          <View style={styles.attachmentPreview}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              {attachments.map((attachment, index) => (
                <Chip
                  key={index}
                  title={attachment.name}
                  icon={{
                    name: attachment.type === 'image' ? 'image' : 'attach-file'
                  }}
                  onPress={() => {
                    setAttachments(attachments.filter((_, i) => i !== index));
                  }}
                  buttonStyle={styles.attachmentPreviewChip}
                />
              ))}
            </ScrollView>
          </View>
        )}

        <View style={styles.inputContainer}>
          <TouchableOpacity
            style={styles.attachButton}
            onPress={() => setShowOptions(true)}
          >
            <Icon name="add" color="#666" />
          </TouchableOpacity>
          
          <TextInput
            style={styles.input}
            value={inputText}
            onChangeText={setInputText}
            placeholder="Type your message..."
            multiline
            maxLength={500}
            onSubmitEditing={sendMessage}
          />
          
          <TouchableOpacity
            style={[styles.sendButton, (!inputText.trim() && attachments.length === 0) && styles.sendButtonDisabled]}
            onPress={sendMessage}
            disabled={!inputText.trim() && attachments.length === 0}
          >
            <Icon
              name="send"
              color={inputText.trim() || attachments.length > 0 ? '#2196F3' : '#ccc'}
            />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>

      <Overlay
        isVisible={showOptions}
        onBackdropPress={() => setShowOptions(false)}
        overlayStyle={styles.overlay}
      >
        <View>
          <Text style={styles.overlayTitle}>Add Attachment</Text>
          <TouchableOpacity
            style={styles.optionButton}
            onPress={() => handleAttachment('photo')}
          >
            <Icon name="photo" color="#2196F3" />
            <Text style={styles.optionText}>Photo</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.optionButton}
            onPress={() => handleAttachment('document')}
          >
            <Icon name="attach-file" color="#2196F3" />
            <Text style={styles.optionText}>Document</Text>
          </TouchableOpacity>
          <Button
            title="Cancel"
            onPress={() => setShowOptions(false)}
            buttonStyle={styles.cancelButton}
          />
        </View>
      </Overlay>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5'
  },
  headerCenter: {
    alignItems: 'center'
  },
  headerTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold'
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#4CAF50',
    marginRight: 4
  },
  statusText: {
    color: '#fff',
    fontSize: 12
  },
  chatContainer: {
    flex: 1
  },
  messagesContainer: {
    flex: 1
  },
  messagesContent: {
    padding: 16
  },
  messageContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'flex-end'
  },
  userMessageContainer: {
    justifyContent: 'flex-end'
  },
  assistantMessageContainer: {
    justifyContent: 'flex-start'
  },
  avatar: {
    marginHorizontal: 8
  },
  messageBubble: {
    maxWidth: '70%',
    padding: 12,
    borderRadius: 16
  },
  userBubble: {
    backgroundColor: '#2196F3',
    borderBottomRightRadius: 4
  },
  assistantBubble: {
    backgroundColor: '#fff',
    borderBottomLeftRadius: 4,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2
  },
  messageText: {
    fontSize: 16,
    color: '#333'
  },
  userMessageText: {
    color: '#fff'
  },
  timestamp: {
    fontSize: 11,
    color: '#666',
    marginTop: 4
  },
  userTimestamp: {
    color: 'rgba(255, 255, 255, 0.8)'
  },
  attachmentsContainer: {
    marginTop: 8
  },
  attachmentChip: {
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    marginBottom: 4
  },
  userAttachmentChip: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)'
  },
  chipTitle: {
    fontSize: 12,
    color: '#666'
  },
  userChipTitle: {
    fontSize: 12,
    color: '#fff'
  },
  suggestedArticlesCard: {
    margin: 0,
    marginTop: 8,
    padding: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 8
  },
  suggestedTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 4
  },
  articleLink: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4
  },
  articleTitle: {
    fontSize: 12,
    color: '#2196F3',
    marginLeft: 4
  },
  typingBubble: {
    padding: 16
  },
  typingIndicator: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  typingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#999',
    marginHorizontal: 2
  },
  attachmentPreview: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0'
  },
  attachmentPreviewChip: {
    marginRight: 8
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 16,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0'
  },
  attachButton: {
    padding: 8,
    marginRight: 8
  },
  input: {
    flex: 1,
    minHeight: 40,
    maxHeight: 100,
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#f5f5f5',
    borderRadius: 20,
    fontSize: 16
  },
  sendButton: {
    padding: 8,
    marginLeft: 8
  },
  sendButtonDisabled: {
    opacity: 0.5
  },
  overlay: {
    width: '80%',
    padding: 20,
    borderRadius: 8
  },
  overlayTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center'
  },
  optionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12
  },
  optionText: {
    fontSize: 16,
    marginLeft: 16
  },
  cancelButton: {
    marginTop: 16,
    backgroundColor: '#666'
  }
});