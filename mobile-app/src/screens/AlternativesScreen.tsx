import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, Text, View } from 'react-native';
import Card from '../components/Card';
import FadeInView from '../components/FadeInView';
import ProductCard from '../components/ProductCard';
import Screen from '../components/Screen';
import { getAlternativesForBarcode } from '../api/client';
import { Alternatives, ProductSummary } from '../types/api';
import { RootScreenProps } from '../navigation/RootNavigator';
import { AppTheme, spacing, useAppTheme } from '../theme';

type Props = RootScreenProps<'Alternatives'>;

type AlternativeRow = {
  key: keyof Alternatives;
  label: string;
  product: ProductSummary | null | undefined;
};

export default function AlternativesScreen({ route, navigation }: Props) {
  const theme = useAppTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const sharedStyles = theme.sharedStyles;
  const { barcode, name } = route.params;
  const [alternatives, setAlternatives] = useState<Alternatives | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    setLoading(true);
    getAlternativesForBarcode(barcode)
      .then((data) => {
        if (active) {
          setAlternatives(data);
        }
      })
      .catch((error) => {
        if (active) {
          Alert.alert('Unable to load alternatives', error instanceof Error ? error.message : 'Check the API.');
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [barcode]);

  const rows = useMemo<AlternativeRow[]>(
    () => [
      {
        key: 'safer_option',
        label: 'Safer option',
        product: alternatives?.safer_option,
      },
      {
        key: 'cheaper_option',
        label: 'Cheaper option',
        product: alternatives?.cheaper_option,
      },
      {
        key: 'same_category_option',
        label: 'Same category',
        product: alternatives?.same_category_option,
      },
    ],
    [alternatives],
  );

  return (
    <Screen>
      <FadeInView>
        <Text style={sharedStyles.screenTitle}>Alternatives</Text>
        <Text style={styles.subtitle}>{name}</Text>
      </FadeInView>

      {loading ? (
        <FadeInView delay={60} style={styles.loaderWrap}>
          <ActivityIndicator color={theme.colors.accent} size="large" />
        </FadeInView>
      ) : (
        <View style={styles.results}>
          {rows.map((row, index) =>
            row.product ? (
              <FadeInView delay={80 + index * 35} key={row.key}>
                <ProductCard
                  label={row.label}
                  product={row.product}
                  onPress={() =>
                    navigation.push('ProductDetail', {
                      barcode: row.product!.barcode,
                      shouldSaveHistory: true,
                    })
                  }
                />
              </FadeInView>
            ) : (
              <FadeInView delay={80 + index * 35} key={row.key}>
                <Card>
                  <Text style={styles.emptyTitle}>{row.label}</Text>
                  <Text style={sharedStyles.body}>No strong match returned.</Text>
                </Card>
              </FadeInView>
            ),
          )}
        </View>
      )}
    </Screen>
  );
}

function createStyles(theme: AppTheme) {
  return StyleSheet.create({
    subtitle: {
      color: theme.colors.muted,
      fontSize: 15,
      lineHeight: 21,
      marginTop: spacing.sm,
      marginBottom: spacing.xl,
    },
    results: {
      gap: spacing.md,
    },
    loaderWrap: {
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 220,
    },
    emptyTitle: {
      color: theme.colors.ink,
      fontSize: 17,
      fontWeight: '700',
      lineHeight: 22,
      marginBottom: spacing.sm,
    },
  });
}
