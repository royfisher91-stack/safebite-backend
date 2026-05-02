import {
  DarkTheme as NavigationDarkTheme,
  DefaultTheme as NavigationDefaultTheme,
  Theme as NavigationTheme,
} from '@react-navigation/native';
import { PropsWithChildren, createContext, createElement, useContext, useMemo } from 'react';
import { ColorSchemeName, Platform, StyleSheet, useColorScheme } from 'react-native';

export const spacing = {
  xs: 6,
  sm: 10,
  md: 14,
  lg: 20,
  xl: 28,
  xxl: 36,
};

export const radii = {
  sm: 10,
  md: 18,
  lg: 24,
  pill: 999,
};

const lightColors = {
  background: '#F4F7F6',
  backgroundElevated: '#FBFCFC',
  surface: '#FFFFFF',
  surfaceMuted: '#EEF4F2',
  surfaceStrong: '#E3ECE8',
  cardOverlay: 'rgba(255,255,255,0.74)',
  ink: '#0E1715',
  text: '#394643',
  muted: '#71807B',
  subtleText: '#8D9A96',
  border: '#D7E1DD',
  borderStrong: '#B9C8C2',
  accent: '#24786A',
  accentSoft: '#DDEDE8',
  safe: '#1E7B58',
  caution: '#9A6A18',
  avoid: '#A44137',
  blue: '#3A6698',
  safeSurface: '#E4F3EC',
  cautionSurface: '#F7EDD9',
  avoidSurface: '#F4E0DD',
  activeSurface: '#E4EDF9',
  imagePlaceholder: '#DCE7E3',
  shadow: '#0E1715',
  tabBar: 'rgba(255,255,255,0.94)',
  inputBackground: '#F7FAF9',
};

const darkColors = {
  background: '#0C1211',
  backgroundElevated: '#111918',
  surface: '#151F1D',
  surfaceMuted: '#1B2724',
  surfaceStrong: '#23302C',
  cardOverlay: 'rgba(21,31,29,0.92)',
  ink: '#F2F7F5',
  text: '#D7E3DE',
  muted: '#9BAAA4',
  subtleText: '#80908A',
  border: '#263633',
  borderStrong: '#334541',
  accent: '#74C8B6',
  accentSoft: '#16352F',
  safe: '#8FE4BE',
  caution: '#F2C168',
  avoid: '#F39C93',
  blue: '#8DB5F0',
  safeSurface: '#143126',
  cautionSurface: '#382B14',
  avoidSurface: '#3C1E1A',
  activeSurface: '#17283B',
  imagePlaceholder: '#20302C',
  shadow: '#000000',
  tabBar: 'rgba(12,18,17,0.96)',
  inputBackground: '#121B19',
};

function buildSharedStyles(colors: typeof lightColors) {
  return StyleSheet.create({
    screenTitle: {
      color: colors.ink,
      fontSize: 34,
      fontWeight: '700',
      lineHeight: 40,
      letterSpacing: 0,
    },
    sectionTitle: {
      color: colors.ink,
      fontSize: 19,
      fontWeight: '700',
      lineHeight: 24,
      letterSpacing: 0,
    },
    body: {
      color: colors.text,
      fontSize: 15,
      lineHeight: 22,
      letterSpacing: 0,
    },
    footnote: {
      color: colors.muted,
      fontSize: 13,
      lineHeight: 18,
      letterSpacing: 0,
    },
    eyebrow: {
      color: colors.accent,
      fontSize: 13,
      fontWeight: '700',
      lineHeight: 18,
      letterSpacing: 0,
      textTransform: 'uppercase',
    },
  });
}

function buildNavigationTheme(colors: typeof lightColors, isDark: boolean): NavigationTheme {
  const base = isDark ? NavigationDarkTheme : NavigationDefaultTheme;
  return {
    ...base,
    dark: isDark,
    colors: {
      ...base.colors,
      background: colors.background,
      card: colors.surface,
      primary: colors.accent,
      text: colors.ink,
      border: colors.border,
      notification: colors.caution,
    },
  };
}

function buildShadow(colors: typeof lightColors, isDark: boolean) {
  return Platform.select({
    ios: {
      shadowColor: colors.shadow,
      shadowOffset: { width: 0, height: isDark ? 10 : 12 },
      shadowOpacity: isDark ? 0.26 : 0.1,
      shadowRadius: isDark ? 22 : 20,
    },
    android: {
      elevation: isDark ? 4 : 3,
    },
    default: {},
  });
}

function buildTheme(colorScheme: ColorSchemeName) {
  const isDark = colorScheme === 'dark';
  const colors = isDark ? darkColors : lightColors;

  return {
    isDark,
    colors,
    spacing,
    radii,
    shadow: buildShadow(colors, isDark),
    sharedStyles: buildSharedStyles(colors),
    navigationTheme: buildNavigationTheme(colors, isDark),
  };
}

export type AppTheme = ReturnType<typeof buildTheme>;

export const colors = lightColors;
export const sharedStyles = buildSharedStyles(lightColors);

const ThemeContext = createContext<AppTheme | null>(null);

export function AppThemeProvider({ children }: PropsWithChildren) {
  const colorScheme = useColorScheme();
  const value = useMemo(() => buildTheme(colorScheme), [colorScheme]);
  return createElement(ThemeContext.Provider, { value }, children);
}

export function useAppTheme(): AppTheme {
  const value = useContext(ThemeContext);
  if (!value) {
    throw new Error('useAppTheme must be used within AppThemeProvider');
  }
  return value;
}
