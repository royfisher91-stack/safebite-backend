import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Animated,
  ImageStyle,
  StyleProp,
  StyleSheet,
  Text,
  View,
  ViewStyle,
} from 'react-native';
import { radii, spacing, useAppTheme } from '../theme';

type Variant = 'card' | 'thumb' | 'hero';

type Props = {
  uri?: string | null;
  label: string;
  variant?: Variant;
  style?: StyleProp<ViewStyle>;
  imageStyle?: StyleProp<ImageStyle>;
};

function initials(label: string): string {
  const parts = label
    .split(/\s+/)
    .map((part) => part.trim())
    .filter(Boolean)
    .slice(0, 2);

  if (!parts.length) {
    return 'SB';
  }

  return parts.map((part) => part[0]?.toUpperCase() || '').join('');
}

function variantStyle(variant: Variant): ViewStyle {
  switch (variant) {
    case 'hero':
      return {
        aspectRatio: 1.14,
        borderRadius: radii.lg,
        width: '100%',
      };
    case 'thumb':
      return {
        borderRadius: radii.md,
        height: 72,
        width: 72,
      };
    case 'card':
    default:
      return {
        borderRadius: radii.md,
        height: 92,
        width: 92,
      };
  }
}

export default function ProductImage({
  uri,
  label,
  variant = 'card',
  style,
  imageStyle,
}: Props) {
  const theme = useAppTheme();
  const fade = useRef(new Animated.Value(0)).current;
  const [loading, setLoading] = useState(Boolean(uri));
  const [hasError, setHasError] = useState(!uri);

  useEffect(() => {
    setLoading(Boolean(uri));
    setHasError(!uri);
    fade.setValue(0);
  }, [uri, fade]);

  const styles = useMemo(
    () =>
      StyleSheet.create({
        frame: {
          alignItems: 'center',
          backgroundColor: theme.colors.imagePlaceholder,
          borderColor: theme.colors.border,
          borderWidth: 1,
          justifyContent: 'center',
          overflow: 'hidden',
        },
        image: {
          height: '100%',
          width: '100%',
        },
        overlayLoader: {
          left: 0,
          position: 'absolute',
          right: 0,
          top: 0,
          bottom: 0,
          alignItems: 'center',
          justifyContent: 'center',
        },
        fallback: {
          alignItems: 'center',
          gap: spacing.xs,
          justifyContent: 'center',
          paddingHorizontal: spacing.sm,
        },
        fallbackGlyph: {
          color: theme.colors.accent,
          fontSize: variant === 'hero' ? 28 : 20,
          fontWeight: '800',
          letterSpacing: 0,
        },
        fallbackText: {
          color: theme.colors.muted,
          fontSize: variant === 'hero' ? 13 : 11,
          fontWeight: '700',
          textAlign: 'center',
          lineHeight: variant === 'hero' ? 18 : 14,
        },
      }),
    [theme, variant],
  );

  const frameStyle = variantStyle(variant);

  return (
    <View style={[styles.frame, frameStyle, style]}>
      {!hasError && !!uri ? (
        <>
          <Animated.Image
            onError={() => {
              setHasError(true);
              setLoading(false);
            }}
            onLoadEnd={() => {
              setLoading(false);
              Animated.timing(fade, {
                duration: 180,
                toValue: 1,
                useNativeDriver: true,
              }).start();
            }}
            resizeMode="cover"
            source={{ uri }}
            style={[styles.image, imageStyle, { opacity: fade }]}
          />
          {loading ? (
            <View pointerEvents="none" style={styles.overlayLoader}>
              <ActivityIndicator color={theme.colors.accent} />
            </View>
          ) : null}
        </>
      ) : (
        <View style={styles.fallback}>
          <Text style={styles.fallbackGlyph}>{initials(label)}</Text>
          {variant === 'hero' ? <Text style={styles.fallbackText}>Image unavailable</Text> : null}
        </View>
      )}
    </View>
  );
}
