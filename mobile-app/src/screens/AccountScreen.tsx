import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, Linking, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import Card from '../components/Card';
import FadeInView from '../components/FadeInView';
import PrimaryButton from '../components/PrimaryButton';
import Screen from '../components/Screen';
import {
  applySubscriptionPromo,
  getEntitlement,
  getSubscription,
} from '../api/client';
import { MainTabScreenProps } from '../navigation/RootNavigator';
import { useAuth } from '../state/AuthContext';
import { Entitlement, SubscriptionStatus } from '../types/api';
import { formatPrice } from '../utils/format';
import { AppTheme, radii, spacing, useAppTheme } from '../theme';

type Props = MainTabScreenProps<'Account'>;
type AuthMode = 'login' | 'register';

const LEGAL_LINKS = [
  { label: 'Privacy Policy', url: 'https://safebite.example/privacy' },
  { label: 'Terms of Use', url: 'https://safebite.example/terms' },
  { label: 'Subscription Terms', url: 'https://safebite.example/subscription-terms' },
  { label: 'Data Deletion Request', url: 'https://safebite.example/delete-account' },
  { label: 'Contact / Support', url: 'https://safebite.example/support' },
];

export default function AccountScreen(_props: Props) {
  const { navigation } = _props;
  const theme = useAppTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const sharedStyles = theme.sharedStyles;
  const auth = useAuth();
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [promoCode, setPromoCode] = useState('');
  const [entitlement, setEntitlement] = useState<Entitlement | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [submittingPromo, setSubmittingPromo] = useState(false);

  const signedIn = auth.isSignedIn;
  const monthlyPrice = formatPrice(subscription?.monthly_price ?? 5);

  async function refreshAccess() {
    if (!auth.isSignedIn) {
      setEntitlement(null);
      setSubscription(null);
      return;
    }

    setLoadingStatus(true);
    try {
      const [nextEntitlement, nextSubscription] = await Promise.all([
        getEntitlement(),
        getSubscription(),
      ]);
      setEntitlement(nextEntitlement);
      setSubscription(nextSubscription);
    } catch {
      Alert.alert('Account', 'Unable to refresh account status.');
    } finally {
      setLoadingStatus(false);
    }
  }

  useEffect(() => {
    refreshAccess();
  }, [auth.isSignedIn]);

  async function submitAuth() {
    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || password.length < 8) {
      Alert.alert('Account', 'Enter an email and a password of at least 8 characters.');
      return;
    }

    try {
      if (mode === 'login') {
        await auth.signIn(cleanEmail, password);
      } else {
        await auth.register(cleanEmail, password);
      }
      setPassword('');
    } catch (error) {
      Alert.alert('Account', error instanceof Error ? error.message : 'Unable to continue.');
    }
  }

  async function handleApplyPromo() {
    const code = promoCode.trim().toUpperCase();
    if (!code) {
      Alert.alert('Promo code', 'Enter a promo code.');
      return;
    }

    try {
      setSubmittingPromo(true);
      const result = await applySubscriptionPromo(code);
      if (!result.applied) {
        Alert.alert('Promo code', result.reason || 'That code could not be applied.');
        return;
      }
      setPromoCode('');
      await auth.refreshUser();
      await refreshAccess();
      Alert.alert('Promo code', 'Access has been updated.');
    } catch {
      Alert.alert('Promo code', 'Unable to apply this code.');
    } finally {
      setSubmittingPromo(false);
    }
  }

  async function openLegalLink(url: string) {
    try {
      await Linking.openURL(url);
    } catch {
      Alert.alert('SafeBite', 'Unable to open this link right now.');
    }
  }

  return (
    <Screen>
      <FadeInView>
        <Text style={sharedStyles.screenTitle}>Account</Text>
        <Text style={styles.subtitle}>
          {signedIn ? auth.user?.email : 'Sign in to track scans, access, saved items, and subscription state.'}
        </Text>
      </FadeInView>

      {!signedIn ? (
        <FadeInView delay={40}>
          <Card style={styles.card}>
            <View style={styles.segmentRow}>
              {(['login', 'register'] as AuthMode[]).map((value) => {
                const selected = mode === value;
                return (
                  <Pressable
                    accessibilityRole="button"
                    key={value}
                    onPress={() => setMode(value)}
                    style={[styles.segmentButton, selected && styles.segmentButtonSelected]}
                  >
                    <Text style={[styles.segmentText, selected && styles.segmentTextSelected]}>
                      {value === 'login' ? 'Login' : 'Register'}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            <Text style={styles.label}>Email</Text>
            <TextInput
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="email-address"
              onChangeText={setEmail}
              placeholder="you@example.com"
              placeholderTextColor={theme.colors.muted}
              style={styles.input}
              value={email}
            />

            <Text style={styles.label}>Password</Text>
            <TextInput
              onChangeText={setPassword}
              placeholder="Password"
              placeholderTextColor={theme.colors.muted}
              secureTextEntry
              style={styles.input}
              value={password}
            />

            <PrimaryButton loading={auth.loading} onPress={submitAuth} style={styles.primaryAction}>
              {mode === 'login' ? 'Login' : 'Create account'}
            </PrimaryButton>
          </Card>
        </FadeInView>
      ) : (
        <>
          <FadeInView delay={40}>
            <Card style={styles.card}>
              <View style={styles.statusHeader}>
                <View>
                  <Text style={sharedStyles.sectionTitle}>
                    {subscription?.active_access ? 'Access active' : 'Free access'}
                  </Text>
                  <Text style={styles.helperText}>
                    {subscription?.plan_code === 'paid_monthly'
                      ? `${monthlyPrice}/month plan`
                      : entitlement?.plan.replace('_', ' ') || 'Free plan'}
                  </Text>
                </View>
                <Text style={styles.statusPill}>
                  {subscription?.status || entitlement?.subscription_status || 'inactive'}
                </Text>
              </View>

              {loadingStatus ? (
                <ActivityIndicator color={theme.colors.accent} style={styles.statusLoader} />
              ) : (
                <View style={styles.meterGrid}>
                  <View style={styles.meterCell}>
                    <Text style={styles.meterValue}>
                      {entitlement?.access_active ? 'Unlimited' : entitlement?.free_scans_remaining ?? 0}
                    </Text>
                    <Text style={styles.meterLabel}>Scans left</Text>
                  </View>
                  <View style={styles.meterCell}>
                    <Text style={styles.meterValue}>{entitlement?.free_scans_used ?? 0}</Text>
                    <Text style={styles.meterLabel}>Free used</Text>
                  </View>
                </View>
              )}

              <PrimaryButton
                onPress={() => navigation.navigate('Billing', { mode: 'subscribe' })}
                style={styles.primaryAction}
              >
                Subscribe {monthlyPrice}/month
              </PrimaryButton>
              <View style={styles.billingActions}>
                <PrimaryButton
                  onPress={() => navigation.navigate('Billing', { mode: 'manage' })}
                  variant="secondary"
                >
                  Manage Subscription
                </PrimaryButton>
                <PrimaryButton
                  onPress={() => navigation.navigate('Billing', { mode: 'restore' })}
                  variant="secondary"
                >
                  Restore Purchases
                </PrimaryButton>
                <PrimaryButton
                  onPress={() => navigation.navigate('Billing', { mode: 'safehome' })}
                  variant="quiet"
                >
                  SafeHome Add-on
                </PrimaryButton>
              </View>
              <Text style={styles.helperText}>
                Paid access is granted only after App Store or Google Play subscription status is verified.
              </Text>
            </Card>
          </FadeInView>

          <FadeInView delay={80}>
            <Card style={styles.card}>
              <Text style={sharedStyles.sectionTitle}>Promo access</Text>
              <TextInput
                autoCapitalize="characters"
                autoCorrect={false}
                onChangeText={(value) => setPromoCode(value.toUpperCase())}
                placeholder="INFLUENCER100"
                placeholderTextColor={theme.colors.muted}
                style={styles.input}
                value={promoCode}
              />
              <PrimaryButton loading={submittingPromo} onPress={handleApplyPromo} variant="secondary">
                Apply code
              </PrimaryButton>
            </Card>
          </FadeInView>

          <PrimaryButton onPress={auth.signOut} style={styles.signOutButton} variant="quiet">
            Logout
          </PrimaryButton>
        </>
      )}

      <FadeInView delay={120}>
        <Card style={styles.card}>
          <Text style={sharedStyles.sectionTitle}>Legal and support</Text>
          <Text style={styles.helperText}>
            Production placeholder pages with solicitor-review TODO markers.
          </Text>
          <View style={styles.legalList}>
            {LEGAL_LINKS.map((item) => (
              <Pressable
                accessibilityRole="link"
                key={item.url}
                onPress={() => openLegalLink(item.url)}
                style={styles.legalLink}
              >
                <Text style={styles.legalLinkText}>{item.label}</Text>
              </Pressable>
            ))}
          </View>
        </Card>
      </FadeInView>
    </Screen>
  );
}

function createStyles(theme: AppTheme) {
  return StyleSheet.create({
    subtitle: {
      color: theme.colors.muted,
      fontSize: 15,
      lineHeight: 22,
      marginTop: spacing.sm,
    },
    card: {
      gap: spacing.md,
      marginTop: spacing.xl,
    },
    segmentRow: {
      backgroundColor: theme.colors.surfaceMuted,
      borderRadius: radii.md,
      flexDirection: 'row',
      padding: 4,
    },
    segmentButton: {
      alignItems: 'center',
      borderRadius: radii.sm,
      flex: 1,
      minHeight: 42,
      justifyContent: 'center',
    },
    segmentButtonSelected: {
      backgroundColor: theme.colors.surface,
    },
    segmentText: {
      color: theme.colors.muted,
      fontSize: 14,
      fontWeight: '800',
    },
    segmentTextSelected: {
      color: theme.colors.accent,
    },
    label: {
      color: theme.colors.text,
      fontSize: 14,
      fontWeight: '700',
    },
    input: {
      backgroundColor: theme.colors.inputBackground,
      borderColor: theme.colors.border,
      borderRadius: radii.md,
      borderWidth: 1,
      color: theme.colors.ink,
      fontSize: 16,
      minHeight: 52,
      paddingHorizontal: 16,
    },
    primaryAction: {
      marginTop: spacing.xs,
    },
    statusHeader: {
      alignItems: 'flex-start',
      flexDirection: 'row',
      gap: spacing.md,
      justifyContent: 'space-between',
    },
    helperText: {
      color: theme.colors.muted,
      fontSize: 14,
      lineHeight: 20,
      marginTop: 4,
      textTransform: 'capitalize',
    },
    statusPill: {
      backgroundColor: theme.colors.accentSoft,
      borderRadius: radii.pill,
      color: theme.colors.accent,
      fontSize: 12,
      fontWeight: '800',
      overflow: 'hidden',
      paddingHorizontal: 12,
      paddingVertical: 7,
      textTransform: 'capitalize',
    },
    statusLoader: {
      marginVertical: spacing.md,
    },
    meterGrid: {
      flexDirection: 'row',
      gap: spacing.sm,
    },
    meterCell: {
      backgroundColor: theme.colors.surfaceMuted,
      borderRadius: radii.md,
      flex: 1,
      padding: spacing.md,
    },
    meterValue: {
      color: theme.colors.ink,
      fontSize: 20,
      fontWeight: '800',
    },
    meterLabel: {
      color: theme.colors.muted,
      fontSize: 12,
      fontWeight: '700',
      marginTop: 4,
    },
    signOutButton: {
      marginTop: spacing.lg,
    },
    billingActions: {
      gap: spacing.sm,
      marginTop: spacing.sm,
    },
    legalList: {
      gap: spacing.sm,
      marginTop: spacing.sm,
    },
    legalLink: {
      backgroundColor: theme.colors.surfaceMuted,
      borderRadius: radii.md,
      paddingHorizontal: spacing.md,
      paddingVertical: 13,
    },
    legalLinkText: {
      color: theme.colors.accent,
      fontSize: 14,
      fontWeight: '800',
    },
  });
}
