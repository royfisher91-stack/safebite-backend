import { CompositeScreenProps, NavigatorScreenParams } from '@react-navigation/native';
import { BottomTabScreenProps, createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import {
  NativeStackScreenProps,
  createNativeStackNavigator,
} from '@react-navigation/native-stack';
import HomeScreen from '../screens/HomeScreen';
import SearchScreen from '../screens/SearchScreen';
import ScannerScreen from '../screens/ScannerScreen';
import SavedScreen from '../screens/SavedScreen';
import HealthScreen from '../screens/HealthScreen';
import AccountScreen from '../screens/AccountScreen';
import BillingScreen from '../screens/BillingScreen';
import ProductDetailScreen from '../screens/ProductDetailScreen';
import AlternativesScreen from '../screens/AlternativesScreen';
import { useAppTheme } from '../theme';

export type MainTabParamList = {
  Home: undefined;
  Search: undefined;
  Scanner: undefined;
  Health: undefined;
  Saved: undefined;
  Account: undefined;
};

export type RootStackParamList = {
  MainTabs: NavigatorScreenParams<MainTabParamList> | undefined;
  ProductDetail: { barcode: string; shouldSaveHistory?: boolean };
  Alternatives: { barcode: string; name: string };
  Billing: { mode: 'subscribe' | 'manage' | 'restore' | 'safehome' };
};

export type RootScreenProps<T extends keyof RootStackParamList> =
  NativeStackScreenProps<RootStackParamList, T>;

export type MainTabScreenProps<T extends keyof MainTabParamList> = CompositeScreenProps<
  BottomTabScreenProps<MainTabParamList, T>,
  NativeStackScreenProps<RootStackParamList>
>;

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

function MainTabs() {
  const theme = useAppTheme();

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: theme.colors.accent,
        tabBarInactiveTintColor: theme.colors.muted,
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '700',
          letterSpacing: 0,
        },
        tabBarStyle: {
          backgroundColor: theme.colors.tabBar,
          borderTopColor: theme.colors.border,
          height: 84,
          paddingBottom: 24,
          paddingTop: 10,
        },
      }}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Search" component={SearchScreen} />
      <Tab.Screen name="Scanner" component={ScannerScreen} />
      <Tab.Screen name="Health" component={HealthScreen} />
      <Tab.Screen name="Saved" component={SavedScreen} />
      <Tab.Screen name="Account" component={AccountScreen} />
    </Tab.Navigator>
  );
}

export default function RootNavigator() {
  const theme = useAppTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerBackTitleVisible: false,
        headerShadowVisible: false,
        headerStyle: {
          backgroundColor: theme.colors.background,
        },
        headerTintColor: theme.colors.accent,
        headerTitleStyle: {
          color: theme.colors.ink,
          fontWeight: '700',
        },
      }}
    >
      <Stack.Screen name="MainTabs" component={MainTabs} options={{ headerShown: false }} />
      <Stack.Screen name="ProductDetail" component={ProductDetailScreen} options={{ title: 'Product' }} />
      <Stack.Screen name="Alternatives" component={AlternativesScreen} options={{ title: 'Alternatives' }} />
      <Stack.Screen name="Billing" component={BillingScreen} options={{ title: 'Billing' }} />
    </Stack.Navigator>
  );
}
