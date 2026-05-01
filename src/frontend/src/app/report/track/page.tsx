'use client';

import { useState } from 'react';
import { fetchReportStatus } from '@/lib/api';
import Image from 'next/image';
import { AlertTriangle, Search, CheckCircle, Clock } from 'lucide-react';
import Link from 'next/link';

export default function ReportTrackerPage() {
    const [reportId, setReportId] = useState('');
    const [statusData, setStatusData] = useState<{ report_id: number; status: string; description: string; created_at: string } | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        if (!reportId.trim()) {
            setError('Please enter a Report ID.');
            return;
        }

        setLoading(true);
        setStatusData(null);
        try {
            const data = await fetchReportStatus(reportId.trim());
            setStatusData(data);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : 'Failed to fetch report status.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center px-4 py-8" style={{ backgroundColor: 'var(--content-bg)' }}>
            <div className="card max-w-lg w-full overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="p-6 text-center" style={{ background: 'var(--bfp-gradient)' }}>
                    <div className="relative w-16 h-16 mx-auto mb-3">
                        <Image src="/bfp-logo.svg" alt="BFP Logo" fill className="object-contain" />
                    </div>
                    <h1 className="text-xl font-bold text-white">Track Emergency Report</h1>
                    <p className="text-sm text-white/70 mt-1">Check the status of your submitted report</p>
                </div>

                {/* Form */}
                <div className="card-body p-6 space-y-6">
                    <form onSubmit={handleSearch} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-primary)' }}>Report Tracking ID</label>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={reportId}
                                    onChange={(e) => setReportId(e.target.value)}
                                    className="flex-1 rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-red-500 focus:outline-none"
                                    style={{ border: '1px solid var(--border-color)', backgroundColor: 'var(--background)', color: 'var(--text-primary)' }}
                                    placeholder="Enter Report ID (e.g., 1024)"
                                    required
                                />
                                <button type="submit" disabled={loading || !reportId.trim()}
                                    className="px-5 py-3 rounded-lg text-white font-bold text-sm disabled:opacity-50 transition-colors flex items-center gap-2"
                                    style={{ background: 'var(--bfp-gradient)' }}>
                                    {loading ? 'Searching...' : <><Search className="w-4 h-4" /> Track</>}
                                </button>
                            </div>
                        </div>

                        {error && (
                            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 text-red-700 text-sm">
                                <AlertTriangle className="w-4 h-4 flex-shrink-0" /> {error}
                            </div>
                        )}
                    </form>

                    {statusData && (
                        <div className="border rounded-lg p-5 mt-6" style={{ backgroundColor: 'white', borderColor: 'var(--border-color)' }}>
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-1">Status</h3>
                                    <div className="flex items-center gap-2">
                                        {statusData.status === 'VERIFIED' ? <CheckCircle className="w-5 h-5 text-green-500" /> : <Clock className="w-5 h-5 text-orange-500" />}
                                        <span className={`text-lg font-bold ${statusData.status === 'VERIFIED' ? 'text-green-600' : 'text-orange-600'}`}>
                                            {statusData.status}
                                        </span>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Date Submitted</h3>
                                    <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                                        {new Date(statusData.created_at).toLocaleString()}
                                    </p>
                                </div>
                            </div>

                            <div>
                                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">Description</h3>
                                <p className="text-sm p-3 bg-gray-800 border rounded-md" style={{ color: 'white', borderColor: 'var(--border-color)' }}>
                                    {statusData.description}
                                </p>
                            </div>

                            {statusData.status === 'VERIFIED' && (
                                <div className="mt-4 p-3 bg-green-50 text-green-800 text-sm rounded-lg flex gap-2 border border-green-200">
                                    <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                    <p>Your report has been verified by the Regional Operations center and responders have been dispatched.</p>
                                </div>
                            )}
                        </div>
                    )}

                    <div className="pt-4 border-t text-center" style={{ borderColor: 'var(--border-color)' }}>
                        <Link href="/report" className="text-sm font-medium text-red-600 hover:text-red-800 transition-colors">
                            &larr; Submit a New Emergency Report
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
