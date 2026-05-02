import { useMemo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Card from './Card';
import ProductImage from './ProductImage';
import StatusPill from './StatusPill';
import { ProductSummary } from '../types/api';
import { formatPrice } from '../utils/format';
import { spacing, useAppTheme } from '../theme';

type Props = {
  product: ProductSummary;
  label?: string;
  onPress: () => void;
};

export default function ProductCard({ product, label, onPress }: Props) {
  const theme = useAppTheme();
  const styles = useMemo(
    () =>
      StyleSheet.create({
        label: {
          color: theme.colors.blue,
          fontSize: 12,
          fontWeight: '800',
          letterSpacing: 0,
          marginBottom: spacing.sm,
          textTransform: 'uppercase',
        },
        shellPressed: {
          transform: [{ scale: 0.988 }],
        },
        header: {
          alignItems: 'flex-start',
          flexDirection: 'row',
          gap: spacing.md,
        },
        imageWrap: {
          flexShrink: 0,
        },
        content: {
          flex: 1,
          minHeight: 92,
        },
        contentTop: {
          alignItems: 'flex-start',
          flexDirection: 'row',
          gap: spacing.sm,
          justifyContent: 'space-between',
          marginBottom: spacing.sm,
        },
        titleBlock: {
          flex: 1,
          paddingRight: spacing.xs,
        },
        brand: {
          color: theme.colors.muted,
          fontSize: 13,
          fontWeight: '700',
          lineHeight: 17,
          marginBottom: 4,
        },
        name: {
          color: theme.colors.ink,
          fontSize: 17,
          fontWeight: '700',
          lineHeight: 22,
          letterSpacing: 0,
        },
        meta: {
          color: theme.colors.muted,
          fontSize: 13,
          lineHeight: 18,
          marginBottom: spacing.sm,
        },
        footer: {
          alignItems: 'flex-end',
          flexDirection: 'row',
          flexWrap: 'wrap',
          gap: spacing.sm,
          justifyContent: 'space-between',
        },
        priceBlock: {
          flex: 1,
          minWidth: 120,
        },
        price: {
          color: theme.colors.ink,
          fontSize: 15,
          fontWeight: '700',
          lineHeight: 20,
        },
        retailer: {
          color: theme.colors.muted,
          fontSize: 12,
          fontWeight: '600',
          lineHeight: 16,
          marginTop: 2,
        },
        score: {
          color: theme.colors.text,
          fontSize: 12,
          fontWeight: '700',
          lineHeight: 16,
        },
      }),
    [theme],
  );

  return (
    <Pressable onPress={onPress}>
      {({ pressed }) => (
        <Card style={pressed ? styles.shellPressed : undefined}>
          {!!label && <Text style={styles.label}>{label}</Text>}
          <View style={styles.header}>
            <ProductImage
              label={product.name}
              style={styles.imageWrap}
              uri={product.image_url}
              variant="card"
            />
            <View style={styles.content}>
              <View style={styles.contentTop}>
                <View style={styles.titleBlock}>
                  <Text style={styles.brand}>{product.brand || 'SafeBite'}</Text>
                  <Text style={styles.name}>{product.name}</Text>
                </View>
                <StatusPill result={product.safety_result} />
              </View>

              <Text style={styles.meta}>
                {product.category || 'Uncategorised'} / {product.subcategory || 'General'}
              </Text>

              <View style={styles.footer}>
                <View style={styles.priceBlock}>
                  <Text style={styles.price}>{formatPrice(product.best_price)}</Text>
                  <Text style={styles.retailer}>
                    {product.cheapest_retailer ? `Best at ${product.cheapest_retailer}` : 'Retailer unavailable'}
                  </Text>
                </View>
                {typeof product.safety_score === 'number' ? (
                  <Text style={styles.score}>Score {product.safety_score}</Text>
                ) : null}
              </View>
            </View>
          </View>
        </Card>
      )}
    </Pressable>
  );
}
