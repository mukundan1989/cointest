"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2 } from "lucide-react"

interface AdfResult {
  stockName: string
  adfStatistic: string
  pValue: string
  criticalValues: { [key: string]: string }
  isStationary: boolean
  conclusion: string
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
      const response = await fetch("/api/adf-test", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tcs_url: tcsUrl,
          hcl_url: hclUrl,
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

  const renderResultCard = (result: AdfResult | undefined) => {
    if (!result) return null
    if (result.error) {
      return (
        <Card className="w-full max-w-md bg-red-50 border-red-200">
          <CardHeader>
            <CardTitle className="text-red-700">{result.stockName} Error</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-600">{result.error}</p>
          </CardContent>
        </Card>
      )
    }
    return (
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>{result.stockName} ADF Test Results</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p>
            <strong>ADF Statistic:</strong> {result.adfStatistic}
          </p>
          <p>
            <strong>p-value:</strong> {result.pValue}
          </p>
          <div>
            <strong>Critical Values:</strong>
            <ul className="list-disc list-inside ml-4">
              {Object.entries(result.criticalValues).map(([key, value]) => (
                <li key={key}>
                  {key}: {value}
                </li>
              ))}
            </ul>
          </div>
          <p className={result.isStationary ? "text-green-600 font-medium" : "text-red-600 font-medium"}>
            {result.conclusion}
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <h1 className="text-3xl font-bold mb-6 text-center">Stock Stationarity Analysis (ADF Test)</h1>
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
          {renderResultCard(results.tcs)}
          {renderResultCard(results.hcltech)}
        </div>
      )}
    </div>
  )
}
