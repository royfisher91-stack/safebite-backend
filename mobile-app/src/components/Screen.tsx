import { PropsWithChildren, useMemo } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { spacing, useAppTheme } from '../theme';

type Props = PropsWithChildren<{
  scroll?: boolean;
}>;

export default function Screen({ children, scroll = true }: Props) {
  const theme = useAppTheme();
  const styles = useMemo(
    () =>
      StyleSheet.create({
        safeArea: {
          flex: 1,
          backgroundColor: theme.colors.background,
        },
        keyboard: {
          flex: 1,
        },
        scrollContent: {
          flexGrow: 1,
        },
        inner: {
          flex: 1,
          paddingHorizontal: spacing.lg,
          paddingTop: spacing.md,
          paddingBottom: spacing.xxl,
        },
        backdrop: {
          backgroundColor: theme.colors.backgroundElevated,
          borderBottomLeftRadius: 36,
          borderBottomRightRadius: 36,
          height: 116,
          left: 0,
          position: 'absolute',
          right: 0,
          top: 0,
        },
        overlay: {
          backgroundColor: theme.colors.accentSoft,
          borderBottomLeftRadius: 36,
          borderBottomRightRadius: 36,
          height: 94,
          left: 0,
          opacity: theme.isDark ? 0.28 : 0.82,
          position: 'absolute',
          right: 0,
          top: 0,
        },
      }),
    [theme],
  );

  const content = <View style={styles.inner}>{children}</View>;

  return (
    <SafeAreaView style={styles.safeArea}>
      <View pointerEvents="none" style={styles.backdrop} />
      <View pointerEvents="none" style={styles.overlay} />
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.keyboard}
      >
        {scroll ? (
          <ScrollView
            contentContainerStyle={styles.scrollContent}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            {content}
          </ScrollView>
        ) : (
          content
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
