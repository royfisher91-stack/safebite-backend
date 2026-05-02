import { useEffect, useMemo, useState } from 'react';
import { Alert, Platform, StyleSheet, Text, View } from 'react-native';
import Card from '../components/Card';
import PrimaryButton from '../components/PrimaryButton';
import Screen from '../components/Screen';
import { getBillingProducts, getSubscription } from '../api/client';
import { RootScreenProps } from '../navigation/RootNavigator';
import { BillingProduct, BillingProductsResponse, SubscriptionStatus } from '../types/api';
import { AppTheme, spacing, useAppTheme } from '../theme';
import { formatPrice } from '../utils/format';

type Props = RootScreenProps<'Billing'>;

const MODE_COPY = {
  subscribe: {
    title: 'Subscribe',
    action: 'Continue with store billing',
    body:
      'SafeBite Core is locked at GBP 5/month. Purchase verification will be handled by App Store or Google Play billing before paid access is granted.',
  },
  manage: {
    title: 'Manage Subscription',
    action: 'Open subscription management',
    body:
      'Subscriptions and cancellation are managed through the App Store on iOS or Google Play on Android, depending on where you subscribed.',
  },
  restore: {
    title: 'Restore Purchases',
    action: 'Restore purchases',
    body:
      'Restore will ask the platform billing SDK for existing purchases, then SafeBite will verify the provider subscription before restoring access.',
  },
  safehome: {
    title: 'SafeHome Add-on',
    action: 'View SafeHome billing',
    body:
      'SafeHome is a paid add-on through safehome_addon. It stays separate from SafeBite food safety checks and requires verified add-on entitlement.',
  },
};

function findProduct(products: BillingProductsResponse | null, productId: string): BillingProduct | null {
  return products?.products.find((item) => item.product_id === productId) ?? null;
}

export default function BillingScreen({ route }: Props) {
  const theme = useAppTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const mode = route.params.mode;
  const copy = MODE_COPY[mode];
  const [products, setProducts] = useState<BillingProductsResponse | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);

  const coreProduct = findProduct(products, 'safebite_core_monthly');
  const safeHomeProduct = findProduct(products, 'safehome_addon');
  const platformLabel = Platform.OS === 'ios' ? 'App Store' : Platform.OS === 'android' ? 'Google Play' : 'web billing';
  const priceText = coreProduct?.price ? `${formatPrice(coreProduct.price)}/month` : 'GBP 5/month';
  const safeHomeEntitlements = subscription?.add_on_entitlements ?? [];
  const safeHomeActive =
    safeHomeEntitlements.includes('safehome_addon') || safeHomeEntitlements.includes('safehome');

  useEffect(() => {
    let mounted = true;
    Promise.all([getBillingProducts(), getSubscription()])
      .then(([nextProducts, nextSubscription]) => {
        if (!mounted) return;
        setProducts(nextProducts);
        setSubscription(nextSubscription);
      })
      .catch(() => {
        if (!mounted) return;
        Alert.alert('Billing', 'Unable to load billing status right now.');
      });
    return () => {
      mounted = false;
    };
  }, []);

  function handlePlaceholderAction() {
    Alert.alert(
      copy.title,
      'Live payment is not connected in this build. No purchase has been made and no paid access has been granted.',
    );
  }

  return (
    <Screen>
      <Text style={theme.sharedStyles.screenTitle}>{copy.title}</Text>
      <Text style={styles.subtitle}>{copy.body}</Text>

      <Card style={styles.card}>
        <Text style={styles.kicker}>SafeBite Core</Text>
        <Text style={styles.price}>{priceText}</Text>
        <Text style={styles.body}>
          Product ID: {coreProduct?.product_id ?? 'safebite_core_monthly'}
        </Text>
        <Text style={styles.body}>Billing provider: {platformLabel}</Text>
        <Text style={styles.body}>
          Status: {subscription?.active_access ? 'active' : subscription?.status ?? 'inactive'}
        </Text>
        <PrimaryButton onPress={handlePlaceholderAction} style={styles.action}>
          {copy.action}
        </PrimaryButton>
      </Card>

      <Card style={styles.card}>
        <Text style={styles.kicker}>SafeHome Add-on</Text>
        <Text style={[styles.gatePill, safeHomeActive && styles.gatePillActive]}>
          {safeHomeActive ? 'Entitlement active' : 'Locked until verified add-on entitlement'}
        </Text>
        <Text style={styles.body}>
          Product ID: {safeHomeProduct?.product_id ?? 'safehome_addon'}
        </Text>
        <Text style={styles.body}>
          SafeHome is paid separately and does not unlock unless the safehome_addon entitlement is verified.
          It does not change SafeBite food safety scoring.
        </Text>
      </Card>

      <Card style={styles.card}>
        <Text style={styles.kicker}>Cancellation</Text>
        <Text style={styles.body}>
          Cancel or manage billing through {platformLabel}. SafeBite updates access only after the
          platform subscription status is verified.
        </Text>
      </Card>
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
      gap: spacing.sm,
      marginTop: spacing.xl,
    },
    kicker: {
      color: theme.colors.accent,
      fontSize: 12,
      fontWeight: '800',
      textTransform: 'uppercase',
    },
    price: {
      color: theme.colors.ink,
      fontSize: 28,
      fontWeight: '900',
    },
    body: {
      color: theme.colors.muted,
      fontSize: 14,
      lineHeight: 21,
    },
    gatePill: {
      alignSelf: 'flex-start',
      backgroundColor: theme.colors.surfaceMuted,
      borderRadius: 999,
      color: theme.colors.muted,
      fontSize: 12,
      fontWeight: '800',
      overflow: 'hidden',
      paddingHorizontal: 12,
      paddingVertical: 7,
    },
    gatePillActive: {
      backgroundColor: theme.colors.safeSurface,
      color: theme.colors.safe,
    },
    action: {
      marginTop: spacing.sm,
    },
  });
}
