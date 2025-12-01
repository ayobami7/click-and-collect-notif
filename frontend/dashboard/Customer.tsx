import React, { useState } from 'react';
import { Camera, Package, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export default function CustomerInterface() {
  const [step, setStep] = useState('input');
  const [customerName, setCustomerName] = useState('');
  const [barcode, setBarcode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [collectionData, setCollectionData] = useState(null);

  const API_URL = 'http://localhost:8000';

  const handleSubmit = async () => {
    if (!customerName.trim() || !barcode.trim()) {
      setError('Please enter both your name and barcode');
      return;
    }

    setLoading(true);
    setError('');
    setStep('scanning');

    try {
      const response = await fetch(`${API_URL}/api/collect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_name: customerName.trim(),
          barcode: barcode.trim()
        })
      });

      const data = await response.json();

      if (response.ok) {
        setCollectionData(data);
        setStep('success');
      } else {
        setError(data.detail || 'Failed to process collection request');
        setStep('error');
      }
    } catch (err) {
      setError('Unable to connect to server. Please try again.');
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep('input');
    setCustomerName('');
    setBarcode('');
    setError('');
    setCollectionData(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleSubmit();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-600 rounded-full mb-4">
            <Package className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            M&S Click & Collect
          </h1>
          <p className="text-gray-600">Scan your barcode to collect your order</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          {step === 'input' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Name
                </label>
                <input
                  type="text"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Enter your full name"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  disabled={loading}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Barcode
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={barcode}
                    onChange={(e) => setBarcode(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="MNS-20251024-X7Y2K9"
                    className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent font-mono"
                    disabled={loading}
                  />
                  <Camera className="absolute right-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Enter the barcode from your confirmation email
                </p>
              </div>

              {error && (
                <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              <button
                onClick={handleSubmit}
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Package className="w-5 h-5" />
                    Request Collection
                  </>
                )}
              </button>

              <div className="pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-500 mb-2 text-center">Quick Test</p>
                <button
                  onClick={() => {
                    setCustomerName('Test User');
                    setBarcode('MNS-20251024-TEST01');
                  }}
                  className="w-full px-3 py-2 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-700"
                >
                  Fill Test Data
                </button>
              </div>
            </div>
          )}

          {step === 'scanning' && (
            <div className="text-center py-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
                <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Processing Request
              </h3>
              <p className="text-gray-600">Notifying staff...</p>
            </div>
          )}

          {step === 'success' && collectionData && (
            <div className="text-center py-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Request Received!
              </h3>
              <p className="text-gray-600 mb-6">
                Staff have been notified. Please wait at the collection point.
              </p>

              <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Customer:</span>
                    <span className="font-medium text-gray-900">{collectionData.customer_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Barcode:</span>
                    <span className="font-mono text-gray-900">{collectionData.barcode}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                      {collectionData.status}
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={handleReset}
                className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-3 px-4 rounded-lg transition-colors"
              >
                Done
              </button>
            </div>
          )}

          {step === 'error' && (
            <div className="text-center py-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
                <AlertCircle className="w-8 h-8 text-red-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Unable to Process
              </h3>
              <p className="text-gray-600 mb-6">{error}</p>

              <button
                onClick={handleReset}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors"
              >
                Try Again
              </button>
            </div>
          )}
        </div>

        <div className="mt-6 text-center text-sm text-gray-600">
          <p>Need help? Contact store staff or call 0800 123 4567</p>
        </div>
      </div>
    </div>
  );
}