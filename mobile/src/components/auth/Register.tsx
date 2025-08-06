import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { Input, Button } from 'react-native-elements';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigation } from '@react-navigation/native';

const Register: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const { register } = useAuth();
  const navigation = useNavigation();

  const handleRegister = async () => {
    if (!name || !email || !password || !confirmPassword) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    if (password.length < 8) {
      Alert.alert('Error', 'Password must be at least 8 characters');
      return;
    }

    try {
      setLoading(true);
      await register(email, password, name);
    } catch (error: any) {
      Alert.alert('Registration Failed', error.message || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView 
        contentContainerStyle={styles.scrollContainer}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.logoContainer}>
          <Icon name="person-add" size={80} color="#3498db" />
          <Text style={styles.appName}>Create Account</Text>
          <Text style={styles.tagline}>Join the NER Platform</Text>
        </View>

        <View style={styles.formContainer}>
          <Input
            placeholder="Full Name"
            leftIcon={<Icon name="person" size={20} color="#95a5a6" />}
            value={name}
            onChangeText={setName}
            autoCapitalize="words"
            containerStyle={styles.inputContainer}
            inputStyle={styles.input}
          />

          <Input
            placeholder="Email"
            leftIcon={<Icon name="email" size={20} color="#95a5a6" />}
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
            containerStyle={styles.inputContainer}
            inputStyle={styles.input}
          />

          <Input
            placeholder="Password"
            leftIcon={<Icon name="lock" size={20} color="#95a5a6" />}
            rightIcon={
              <Icon 
                name={showPassword ? 'visibility-off' : 'visibility'} 
                size={20} 
                color="#95a5a6"
                onPress={() => setShowPassword(!showPassword)}
              />
            }
            value={password}
            onChangeText={setPassword}
            secureTextEntry={!showPassword}
            containerStyle={styles.inputContainer}
            inputStyle={styles.input}
          />

          <Input
            placeholder="Confirm Password"
            leftIcon={<Icon name="lock-outline" size={20} color="#95a5a6" />}
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            secureTextEntry={!showPassword}
            containerStyle={styles.inputContainer}
            inputStyle={styles.input}
          />

          <Button
            title="Create Account"
            loading={loading}
            buttonStyle={styles.registerButton}
            titleStyle={styles.registerButtonText}
            onPress={handleRegister}
          />

          <View style={styles.footer}>
            <Text style={styles.footerText}>Already have an account? </Text>
            <Text 
              style={styles.loginLink}
              onPress={() => navigation.navigate('Login' as never)}
            >
              Sign In
            </Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  appName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2c3e50',
    marginTop: 15,
  },
  tagline: {
    fontSize: 14,
    color: '#7f8c8d',
    marginTop: 5,
  },
  formContainer: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  inputContainer: {
    marginBottom: 15,
  },
  input: {
    fontSize: 16,
  },
  registerButton: {
    backgroundColor: '#27ae60',
    borderRadius: 25,
    paddingVertical: 15,
    marginTop: 10,
  },
  registerButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 20,
  },
  footerText: {
    color: '#7f8c8d',
    fontSize: 14,
  },
  loginLink: {
    color: '#3498db',
    fontSize: 14,
    fontWeight: 'bold',
  },
});

export default Register;