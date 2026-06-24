export const REGION_COORDINATES: Record<string, [number, number]> = {
  Europe: [10.0, 50.0],
  "United States": [-95.7129, 37.0902],
  China: [104.1954, 35.8617],
  Japan: [138.2529, 36.2048],
  Australia: [133.7751, -25.2744],
  India: [78.9629, 20.5937],
  Singapore: [103.8198, 1.3521],
  Canada: [-106.3468, 56.1304],
  "Latin America": [-60.0, -15.0],
  Africa: [20.0, 0.0],
};

// Calculate bubble radius based on TWh value
export function calculateBubbleRadius(
  value: number | null | undefined,
  min: number | null | undefined,
  max: number | null | undefined
): number {
  let displayValue = 0;
  if (value != null) {
    displayValue = value;
  } else if (min != null && max != null) {
    displayValue = (min + max) / 2;
  } else if (min != null) {
    displayValue = min;
  } else {
    return 2; // Default minimal size for unknown/null
  }

  // Basic scaling: e.g., max is around 500 TWh (China proj)
  // Let's scale from 2px up to 24px radius
  const minSize = 4;
  const maxSize = 24;
  const maxExpectedValue = 500;

  // Use a square root scale for area proportionality
  const scale = Math.sqrt(displayValue / maxExpectedValue);
  const size = minSize + scale * (maxSize - minSize);

  return Math.min(Math.max(size, minSize), maxSize);
}
