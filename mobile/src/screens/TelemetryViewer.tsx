import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { getUxEvents, clearUxEvents } from '../utils/uxTelemetry';

const TelemetryViewer: React.FC = () => {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);

  const load = async () => {
    setLoading(true);
    const evs = await getUxEvents();
    setEvents(evs.reverse());
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const handleClear = async () => {
    setClearing(true);
    await clearUxEvents();
    await load();
    setClearing(false);
  };

  return (
    <View style={{ flex: 1, backgroundColor: '#fff' }}>
      <View style={{ paddingHorizontal: 16, paddingVertical: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderBottomWidth: 1, borderBottomColor: '#eee' }}>
        <Text style={{ fontSize: 18, fontWeight: 'bold' }}>Telemetry</Text>
        <View style={{ flexDirection: 'row' }}>
          <TouchableOpacity accessibilityLabel="Refresh" onPress={load} style={{ marginRight: 16 }}>
            <Icon name="refresh" size={22} color="#3498db" />
          </TouchableOpacity>
          <TouchableOpacity accessibilityLabel="Clear" onPress={handleClear} disabled={clearing}>
            <Icon name="delete-forever" size={22} color={clearing ? '#aaa' : '#e74c3c'} />
          </TouchableOpacity>
        </View>
      </View>
      {loading ? (
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
          <ActivityIndicator size="large" color="#3498db" />
        </View>
      ) : (
        <ScrollView contentContainerStyle={{ padding: 16 }}>
          {events.length === 0 ? (
            <Text style={{ color: '#666' }}>No events captured yet.</Text>
          ) : (
            events.map((e, idx) => (
              <View key={idx} style={{ padding: 12, borderWidth: 1, borderColor: '#eee', borderRadius: 8, marginBottom: 10 }}>
                <Text style={{ fontWeight: '600' }}>{e.event}</Text>
                <Text style={{ color: '#999', fontSize: 12 }}>{new Date(e.ts || e.srv_ts || Date.now()).toLocaleString()}</Text>
                <Text style={{ marginTop: 6, color: '#333' }}>
                  {(() => {
                    try { return JSON.stringify(e, null, 2); } catch { return String(e); }
                  })()}
                </Text>
              </View>
            ))
          )}
        </ScrollView>
      )}
    </View>
  );
};

export default TelemetryViewer;

