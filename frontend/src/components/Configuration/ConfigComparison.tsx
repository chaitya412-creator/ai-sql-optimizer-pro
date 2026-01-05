import { ArrowRight, TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface ConfigComparisonProps {
  parameter: string;
  currentValue: string;
  recommendedValue: string;
  impactEstimate?: string;
  unit?: string;
}

export default function ConfigComparison({
  parameter,
  currentValue,
  recommendedValue,
  impactEstimate,
  unit = '',
}: ConfigComparisonProps) {
  const parseValue = (value: string): number => {
    // Try to extract numeric value from string
    const match = value.match(/(\d+\.?\d*)/);
    return match ? parseFloat(match[1]) : 0;
  };

  const currentNum = parseValue(currentValue);
  const recommendedNum = parseValue(recommendedValue);
  const percentChange =
    currentNum > 0 ? ((recommendedNum - currentNum) / currentNum) * 100 : 0;

  const getChangeIcon = () => {
    if (Math.abs(percentChange) < 1) {
      return <Minus className="w-5 h-5 text-gray-500" />;
    }
    return percentChange > 0 ? (
      <TrendingUp className="w-5 h-5 text-green-600 dark:text-green-400" />
    ) : (
      <TrendingDown className="w-5 h-5 text-red-600 dark:text-red-400" />
    );
  };

  const getChangeColor = () => {
    if (Math.abs(percentChange) < 1) {
      return 'text-gray-600 dark:text-gray-400';
    }
    return percentChange > 0
      ? 'text-green-600 dark:text-green-400'
      : 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      {/* Parameter Name */}
      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">
        {parameter}
      </h4>

      {/* Comparison */}
      <div className="flex items-center justify-between space-x-4">
        {/* Current Value */}
        <div className="flex-1">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Current</p>
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
            <p className="text-lg font-mono font-semibold text-gray-900 dark:text-white">
              {currentValue}
              {unit && <span className="text-sm text-gray-500 ml-1">{unit}</span>}
            </p>
          </div>
        </div>

        {/* Arrow & Change */}
        <div className="flex flex-col items-center space-y-1">
          <ArrowRight className="w-6 h-6 text-gray-400" />
          {Math.abs(percentChange) >= 1 && (
            <div className="flex items-center space-x-1">
              {getChangeIcon()}
              <span className={`text-xs font-semibold ${getChangeColor()}`}>
                {percentChange > 0 ? '+' : ''}
                {percentChange.toFixed(1)}%
              </span>
            </div>
          )}
        </div>

        {/* Recommended Value */}
        <div className="flex-1">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Recommended</p>
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg p-3 border border-blue-200 dark:border-blue-800">
            <p className="text-lg font-mono font-semibold text-blue-600 dark:text-blue-400">
              {recommendedValue}
              {unit && <span className="text-sm text-blue-500 ml-1">{unit}</span>}
            </p>
          </div>
        </div>
      </div>

      {/* Impact Estimate */}
      {impactEstimate && (
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-xs font-medium text-blue-900 dark:text-blue-100 mb-1">
            Expected Impact:
          </p>
          <p className="text-xs text-blue-700 dark:text-blue-300">{impactEstimate}</p>
        </div>
      )}
    </div>
  );
}
