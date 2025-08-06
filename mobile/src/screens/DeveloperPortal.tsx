import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  FlatList,
  Alert,
  Modal,
  TextInput,
  Clipboard,
} from 'react-native';
import { Card, Button, Badge, ListItem, Input, CheckBox } from 'react-native-elements';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { apiClient, ApiKey, Webhook } from '../services/apiClient';

const DeveloperPortal: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [usage, setUsage] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'keys' | 'webhooks' | 'docs'>('keys');
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [newApiKey, setNewApiKey] = useState<{ name: string; scopes: string[] }>({
    name: '',
    scopes: [],
  });
  const [generatedKey, setGeneratedKey] = useState<string>('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [keysData, webhooksData, usageData] = await Promise.all([
        apiClient.getApiKeys(),
        apiClient.getWebhooks(),
        apiClient.getApiUsage(),
      ]);
      setApiKeys(keysData);
      setWebhooks(webhooksData);
      setUsage(usageData);
    } catch (error) {
      Alert.alert('Error', 'Failed to load developer data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleCreateApiKey = async () => {
    if (!newApiKey.name || newApiKey.scopes.length === 0) {
      Alert.alert('Error', 'Please provide a name and select at least one scope');
      return;
    }

    try {
      const response = await apiClient.createApiKey({
        name: newApiKey.name,
        scopes: newApiKey.scopes,
        rate_limit: 1000,
      });
      
      setGeneratedKey(response.key);
      await loadData();
    } catch (error) {
      Alert.alert('Error', 'Failed to create API key');
    }
  };

  const handleCopyKey = () => {
    Clipboard.setString(generatedKey);
    Alert.alert('Success', 'API key copied to clipboard');
  };

  const handleRevokeKey = (keyId: string) => {
    Alert.alert(
      'Revoke API Key',
      'Are you sure you want to revoke this API key? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Revoke',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiClient.revokeApiKey(keyId);
              await loadData();
              Alert.alert('Success', 'API key revoked');
            } catch (error) {
              Alert.alert('Error', 'Failed to revoke API key');
            }
          },
        },
      ]
    );
  };

  const renderUsageCard = () => (
    <Card containerStyle={styles.usageCard}>
      <Text style={styles.cardTitle}>API Usage (Last 30 Days)</Text>
      {usage && (
        <View style={styles.usageStats}>
          <View style={styles.usageStat}>
            <Text style={styles.usageValue}>{usage.total_requests || 0}</Text>
            <Text style={styles.usageLabel}>Total Requests</Text>
          </View>
          <View style={styles.usageStat}>
            <Text style={[styles.usageValue, { color: '#e74c3c' }]}>
              {usage.total_errors || 0}
            </Text>
            <Text style={styles.usageLabel}>Errors</Text>
          </View>
          <View style={styles.usageStat}>
            <Text style={[styles.usageValue, { color: '#27ae60' }]}>
              {usage.error_rate?.toFixed(1) || 0}%
            </Text>
            <Text style={styles.usageLabel}>Success Rate</Text>
          </View>
        </View>
      )}
    </Card>
  );

  const renderApiKeyItem = ({ item }: { item: ApiKey }) => (
    <Card containerStyle={styles.apiKeyCard}>
      <View style={styles.keyHeader}>
        <View style={{ flex: 1 }}>
          <Text style={styles.keyName}>{item.name}</Text>
          <Text style={styles.keyId}>Key ID: {item.key_id.substring(0, 8)}...</Text>
        </View>
        <TouchableOpacity onPress={() => handleRevokeKey(item.key_id)}>
          <Icon name="delete" size={24} color="#e74c3c" />
        </TouchableOpacity>
      </View>
      
      <View style={styles.keyScopes}>
        {item.scopes.map(scope => (
          <Badge
            key={scope}
            value={scope}
            badgeStyle={styles.scopeBadge}
            textStyle={styles.scopeText}
          />
        ))}
      </View>
      
      <View style={styles.keyFooter}>
        <Text style={styles.keyMeta}>Rate limit: {item.rate_limit}/hour</Text>
        <Text style={styles.keyMeta}>
          Last used: {item.last_used_at ? new Date(item.last_used_at).toLocaleDateString() : 'Never'}
        </Text>
      </View>
    </Card>
  );

  const renderWebhookItem = ({ item }: { item: Webhook }) => (
    <Card containerStyle={styles.webhookCard}>
      <View style={styles.webhookHeader}>
        <Icon 
          name="circle" 
          size={12} 
          color={item.is_active ? '#27ae60' : '#95a5a6'} 
          style={{ marginRight: 10 }}
        />
        <Text style={styles.webhookUrl} numberOfLines={1}>
          {item.url}
        </Text>
      </View>
      
      <View style={styles.webhookEvents}>
        {item.events.map(event => (
          <Badge
            key={event}
            value={event}
            badgeStyle={styles.eventBadge}
            textStyle={styles.eventText}
          />
        ))}
      </View>
      
      <View style={styles.webhookFooter}>
        <Text style={styles.webhookMeta}>
          Failures: {item.failure_count}
        </Text>
        <TouchableOpacity>
          <Text style={styles.webhookAction}>Edit</Text>
        </TouchableOpacity>
      </View>
    </Card>
  );

  const renderApiKeys = () => (
    <>
      <FlatList
        data={apiKeys}
        renderItem={renderApiKeyItem}
        keyExtractor={item => item.key_id}
        contentContainerStyle={styles.keysList}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Icon name="vpn-key" size={48} color="#bdc3c7" />
            <Text style={styles.emptyText}>No API keys yet</Text>
          </View>
        }
      />
      
      <Button
        title="Create API Key"
        icon={<Icon name="add" size={20} color="white" style={{ marginRight: 10 }} />}
        buttonStyle={styles.createButton}
        onPress={() => setShowApiKeyModal(true)}
      />
    </>
  );

  const renderWebhooks = () => (
    <>
      <FlatList
        data={webhooks}
        renderItem={renderWebhookItem}
        keyExtractor={item => item.webhook_id}
        contentContainerStyle={styles.webhooksList}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Icon name="webhook" size={48} color="#bdc3c7" />
            <Text style={styles.emptyText}>No webhooks configured</Text>
          </View>
        }
      />
      
      <Button
        title="Add Webhook"
        icon={<Icon name="add" size={20} color="white" style={{ marginRight: 10 }} />}
        buttonStyle={styles.createButton}
        onPress={() => Alert.alert('Add Webhook', 'Webhook creation coming soon!')}
      />
    </>
  );

  const renderDocumentation = () => (
    <ScrollView style={styles.docsContainer}>
      <Card containerStyle={styles.docsCard}>
        <Text style={styles.docsTitle}>Getting Started</Text>
        <Text style={styles.docsText}>
          Welcome to the NER Platform API! Our RESTful API provides programmatic access to all platform features.
        </Text>
        
        <Text style={styles.docsSubtitle}>Base URL</Text>
        <View style={styles.codeBlock}>
          <Text style={styles.codeText}>https://api.nerplatform.com/v1</Text>
        </View>
        
        <Text style={styles.docsSubtitle}>Authentication</Text>
        <Text style={styles.docsText}>
          All API requests require authentication using an API key in the Authorization header:
        </Text>
        <View style={styles.codeBlock}>
          <Text style={styles.codeText}>Authorization: Bearer YOUR_API_KEY</Text>
        </View>
      </Card>

      <Card containerStyle={styles.docsCard}>
        <Text style={styles.docsTitle}>Available SDKs</Text>
        
        <ListItem bottomDivider>
          <Icon name="code" size={24} color="#3498db" />
          <ListItem.Content>
            <ListItem.Title>Python SDK</ListItem.Title>
            <ListItem.Subtitle>pip install nerplatform</ListItem.Subtitle>
          </ListItem.Content>
          <ListItem.Chevron />
        </ListItem>
        
        <ListItem bottomDivider>
          <Icon name="code" size={24} color="#f39c12" />
          <ListItem.Content>
            <ListItem.Title>JavaScript SDK</ListItem.Title>
            <ListItem.Subtitle>npm install @nerplatform/sdk</ListItem.Subtitle>
          </ListItem.Content>
          <ListItem.Chevron />
        </ListItem>
        
        <ListItem>
          <Icon name="code" size={24} color="#27ae60" />
          <ListItem.Content>
            <ListItem.Title>Go SDK</ListItem.Title>
            <ListItem.Subtitle>go get github.com/nerplatform/go-sdk</ListItem.Subtitle>
          </ListItem.Content>
          <ListItem.Chevron />
        </ListItem>
      </Card>
    </ScrollView>
  );

  const renderTabs = () => (
    <View style={styles.tabContainer}>
      <TouchableOpacity
        style={[styles.tab, selectedTab === 'keys' && styles.activeTab]}
        onPress={() => setSelectedTab('keys')}
      >
        <Icon 
          name="vpn-key" 
          size={20} 
          color={selectedTab === 'keys' ? '#3498db' : '#95a5a6'} 
        />
        <Text style={[styles.tabText, selectedTab === 'keys' && styles.activeTabText]}>
          API Keys
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tab, selectedTab === 'webhooks' && styles.activeTab]}
        onPress={() => setSelectedTab('webhooks')}
      >
        <Icon 
          name="webhook" 
          size={20} 
          color={selectedTab === 'webhooks' ? '#3498db' : '#95a5a6'} 
        />
        <Text style={[styles.tabText, selectedTab === 'webhooks' && styles.activeTabText]}>
          Webhooks
        </Text>
      </TouchableOpacity>
      
      <TouchableOpacity
        style={[styles.tab, selectedTab === 'docs' && styles.activeTab]}
        onPress={() => setSelectedTab('docs')}
      >
        <Icon 
          name="description" 
          size={20} 
          color={selectedTab === 'docs' ? '#3498db' : '#95a5a6'} 
        />
        <Text style={[styles.tabText, selectedTab === 'docs' && styles.activeTabText]}>
          Docs
        </Text>
      </TouchableOpacity>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#3498db" />
        <Text style={styles.loadingText}>Loading developer portal...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
      >
        {renderUsageCard()}
        {renderTabs()}
        
        {selectedTab === 'keys' && renderApiKeys()}
        {selectedTab === 'webhooks' && renderWebhooks()}
        {selectedTab === 'docs' && renderDocumentation()}
      </ScrollView>

      {/* API Key Creation Modal */}
      <Modal
        visible={showApiKeyModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => {
          setShowApiKeyModal(false);
          setGeneratedKey('');
          setNewApiKey({ name: '', scopes: [] });
        }}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            {generatedKey ? (
              <>
                <Text style={styles.modalTitle}>API Key Created!</Text>
                <Text style={styles.modalText}>
                  Make sure to copy your API key now. You won't be able to see it again!
                </Text>
                
                <View style={styles.keyDisplay}>
                  <Text style={styles.generatedKey}>{generatedKey}</Text>
                  <TouchableOpacity onPress={handleCopyKey} style={styles.copyButton}>
                    <Icon name="content-copy" size={20} color="#3498db" />
                  </TouchableOpacity>
                </View>
                
                <Button
                  title="Done"
                  buttonStyle={styles.modalButton}
                  onPress={() => {
                    setShowApiKeyModal(false);
                    setGeneratedKey('');
                    setNewApiKey({ name: '', scopes: [] });
                  }}
                />
              </>
            ) : (
              <>
                <Text style={styles.modalTitle}>Create API Key</Text>
                
                <Input
                  placeholder="Key Name"
                  value={newApiKey.name}
                  onChangeText={(text) => setNewApiKey({ ...newApiKey, name: text })}
                  containerStyle={styles.input}
                />
                
                <Text style={styles.scopesTitle}>Scopes</Text>
                {['read', 'write', 'delete'].map(scope => (
                  <CheckBox
                    key={scope}
                    title={scope.charAt(0).toUpperCase() + scope.slice(1)}
                    checked={newApiKey.scopes.includes(scope)}
                    onPress={() => {
                      const newScopes = newApiKey.scopes.includes(scope)
                        ? newApiKey.scopes.filter(s => s !== scope)
                        : [...newApiKey.scopes, scope];
                      setNewApiKey({ ...newApiKey, scopes: newScopes });
                    }}
                    containerStyle={styles.checkbox}
                  />
                ))}
                
                <View style={styles.modalButtons}>
                  <Button
                    title="Cancel"
                    type="outline"
                    buttonStyle={styles.cancelButton}
                    onPress={() => {
                      setShowApiKeyModal(false);
                      setNewApiKey({ name: '', scopes: [] });
                    }}
                  />
                  <Button
                    title="Create"
                    buttonStyle={styles.createModalButton}
                    onPress={handleCreateApiKey}
                  />
                </View>
              </>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  usageCard: {
    margin: 15,
    borderRadius: 10,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#2c3e50',
  },
  usageStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  usageStat: {
    alignItems: 'center',
  },
  usageValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#3498db',
  },
  usageLabel: {
    fontSize: 12,
    color: '#7f8c8d',
    marginTop: 5,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: 'white',
    elevation: 2,
    marginBottom: 15,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    gap: 5,
  },
  activeTab: {
    borderBottomWidth: 3,
    borderBottomColor: '#3498db',
  },
  tabText: {
    fontSize: 14,
    color: '#95a5a6',
  },
  activeTabText: {
    color: '#3498db',
    fontWeight: '600',
  },
  keysList: {
    padding: 15,
  },
  apiKeyCard: {
    marginBottom: 10,
    borderRadius: 10,
  },
  keyHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  keyName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#2c3e50',
  },
  keyId: {
    fontSize: 12,
    color: '#7f8c8d',
    marginTop: 2,
  },
  keyScopes: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 5,
    marginBottom: 10,
  },
  scopeBadge: {
    backgroundColor: '#3498db',
    borderRadius: 12,
    paddingHorizontal: 10,
  },
  scopeText: {
    fontSize: 12,
  },
  keyFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  keyMeta: {
    fontSize: 12,
    color: '#95a5a6',
  },
  webhooksList: {
    padding: 15,
  },
  webhookCard: {
    marginBottom: 10,
    borderRadius: 10,
  },
  webhookHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  webhookUrl: {
    flex: 1,
    fontSize: 14,
    color: '#2c3e50',
  },
  webhookEvents: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 5,
    marginBottom: 10,
  },
  eventBadge: {
    backgroundColor: '#ecf0f1',
    borderRadius: 12,
    paddingHorizontal: 10,
  },
  eventText: {
    fontSize: 12,
    color: '#7f8c8d',
  },
  webhookFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  webhookMeta: {
    fontSize: 12,
    color: '#95a5a6',
  },
  webhookAction: {
    fontSize: 14,
    color: '#3498db',
  },
  createButton: {
    margin: 15,
    backgroundColor: '#3498db',
    borderRadius: 25,
    paddingVertical: 12,
  },
  docsContainer: {
    flex: 1,
  },
  docsCard: {
    margin: 15,
    borderRadius: 10,
  },
  docsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#2c3e50',
  },
  docsSubtitle: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 15,
    marginBottom: 10,
    color: '#34495e',
  },
  docsText: {
    fontSize: 14,
    color: '#7f8c8d',
    lineHeight: 20,
    marginBottom: 10,
  },
  codeBlock: {
    backgroundColor: '#2c3e50',
    padding: 15,
    borderRadius: 8,
    marginBottom: 15,
  },
  codeText: {
    color: 'white',
    fontFamily: 'monospace',
    fontSize: 14,
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 16,
    color: '#95a5a6',
    marginTop: 10,
  },
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    width: '90%',
    maxWidth: 400,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#2c3e50',
    textAlign: 'center',
  },
  modalText: {
    fontSize: 14,
    color: '#7f8c8d',
    marginBottom: 20,
    textAlign: 'center',
  },
  input: {
    marginBottom: 20,
  },
  scopesTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 10,
    color: '#2c3e50',
  },
  checkbox: {
    backgroundColor: 'transparent',
    borderWidth: 0,
    paddingHorizontal: 0,
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 20,
  },
  cancelButton: {
    flex: 1,
    marginRight: 10,
    borderColor: '#3498db',
  },
  createModalButton: {
    flex: 1,
    marginLeft: 10,
    backgroundColor: '#3498db',
  },
  modalButton: {
    backgroundColor: '#3498db',
    borderRadius: 25,
    paddingVertical: 12,
  },
  keyDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    padding: 15,
    borderRadius: 8,
    marginBottom: 20,
  },
  generatedKey: {
    flex: 1,
    fontFamily: 'monospace',
    fontSize: 12,
    color: '#2c3e50',
  },
  copyButton: {
    padding: 5,
  },
});

export default DeveloperPortal;