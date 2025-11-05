import React from 'react'
import { View, Text } from 'react-native'

type Metric = { metric_name: string; value: number; confidence: number }

type Props = {
  metrics: Metric[]
}

export default function Scoreboard({ metrics }: Props) {
  return (
    <View>
      <Text>Metrics</Text>
      {metrics.map((m) => (
        <Text key={m.metric_name}>{`${m.metric_name}: ${m.value.toFixed(2)} (${(
          m.confidence * 100
        ).toFixed(0)}%)`}</Text>
      ))}
    </View>
  )
}








