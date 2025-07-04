"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2 } from "lucide-react"

interface AdfResult {
  t_stat: number
  alpha: number
  beta: number
  lag_used: number
  critical_values: { [key: string]: number }
  series_length: number
  error?: string
}

interface AdfTestResponse {
  tcs?: AdfResult
  hcltech?: AdfResult
}

export default function AdfTestPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<AdfTestResponse | null>(null)

  const tcsUrl =
    "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/TCS.NS_data-ZhYlsQFTTT8cA9vDZXyai7YigVPqJf.csv"
  const hclUrl =
    "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/HCLTECH.NS_data-ZwOgKR4HqK1WnqHtuxYYMKc1QNlyKs.csv"

  const runAdfTest = async () => {
    setLoading(true)
    setError(null)
    setResults(null)
    try {
      const response = await fetch("/api/adf", {
        // Call the new pure Python API
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tcs_url: tcsUrl,
          hcl_url: hclUrl,
          lags: 0, // You can make this dynamic if needed
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || "Failed to fetch ADF test results.")
      }

      const data: AdfTestResponse = await response.json()
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred.")
    } finally {
      setLoading(false)
    }
  }

  const renderResultCard = (stockName: string, result: AdfResult | undefined) => {
    if (!result) return null
    if (result.error) {
      return (
        <Card className="w-full max-w-md bg-red-50 border-red-200">
          <CardHeader>
            <CardTitle className="text-red-700">{stockName} Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-600">{result.error}</p>
          </CardContent>
        </Card>
      )
    }

    // Determine stationarity based on t-statistic vs critical values
    let isStationary = false
    let conclusion = "Cannot definitively determine stationarity without p-value."
    if (result.t_stat < result.critical_values["5%"]) {
      // Common threshold
      isStationary = true
      conclusion = `The t-statistic (${result.t_stat}) is less than the 5% critical value (${result.critical_values["5%"]}). This suggests the series might be stationary.`
    } else {
      conclusion = `The t-statistic (${result.t_stat}) is greater than the 5% critical value (${result.critical_values["5%"]}). This suggests the series might be non-stationary.`
    }

    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{stockName} ADF Test Results (Pure Python)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p>
            <strong>ADF T-Statistic:</strong> {result.t_stat}
          </p>
          <p>
            <strong>Alpha (α):</strong> {result.alpha}
          </p>
          <p>
            <strong>Beta (β):</strong> {result.beta}
          </p>
          <p>
            <strong>Lags Used:</strong> {result.lag_used}
          </p>
          <p>
            <strong>Series Length:</strong> {result.series_length}
          </p>
          <div>
            <strong>Approximate Critical Values:</strong>
            <ul className="list-disc list-inside ml-4">
              {Object.entries(result.critical_values).map(([key, value]) => (
                <li key={key} key={key}>
                  {key}: {value}
                </li>
              ))}
            </ul>
          </div>
          <p className={isStationary ? "text-green-600 font-medium" : "text-red-600 font-medium"}>{conclusion}</p>
          <p className="text-sm text-gray-500">
            Note: This pure Python implementation provides approximate critical values and does not calculate a p-value.
            For a definitive statistical conclusion, a full statistical library (like `statsmodels` or `arch`) is
            recommended.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">Stock Stationarity Analysis (Pure Python ADF)</h1>
      <Button onClick={runAdfTest} disabled={loading} className="mb-8">
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Running ADF Test...
          </>
        ) : (
          "Run ADF Test"
        )}
      </Button>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}

      {results && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">
          {renderResultCard("TCS.NS", results.tcs)}
          {renderResultCard("HCLTECH.NS", results.hcltech)}
        </div>
      )}
    </div>
  )
}
