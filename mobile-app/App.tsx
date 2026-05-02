import { NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import RootNavigator from './src/navigation/RootNavigator';
import { AuthProvider } from './src/state/AuthContext';
import { HealthPreferencesProvider } from './src/state/HealthPreferencesContext';
import { AppThemeProvider, useAppTheme } from './src/theme';

function AppShell() {
  const theme = useAppTheme();

  return (
    <NavigationContainer theme={theme.navigationTheme}>
      <StatusBar style={theme.isDark ? 'light' : 'dark'} />
      <RootNavigator />
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <AppThemeProvider>
      <AuthProvider>
        <HealthPreferencesProvider>
          <AppShell />
        </HealthPreferencesProvider>
      </AuthProvider>
    </AppThemeProvider>
  );
}
