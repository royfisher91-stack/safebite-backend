import { PropsWithChildren, useEffect, useMemo, useRef } from 'react';
import { Animated, StyleProp, ViewStyle } from 'react-native';

type Props = PropsWithChildren<{
  delay?: number;
  duration?: number;
  distance?: number;
  style?: StyleProp<ViewStyle>;
}>;

export default function FadeInView({
  children,
  delay = 0,
  duration = 240,
  distance = 12,
  style,
}: Props) {
  const opacity = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(distance)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, {
        delay,
        duration,
        toValue: 1,
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        delay,
        duration,
        toValue: 0,
        useNativeDriver: true,
      }),
    ]).start();
  }, [delay, distance, duration, opacity, translateY]);

  const animatedStyle = useMemo(
    () => ({
      opacity,
      transform: [{ translateY }],
    }),
    [opacity, translateY],
  );

  return <Animated.View style={[animatedStyle, style]}>{children}</Animated.View>;
}
