import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { getKnowledgeFiles, uploadKnowledgeFile, getKnowledgePreview, deleteKnowledgeFile } from '../../api/client';
import { Upload, FileText, CheckCircle, AlertCircle, RefreshCw, Eye, X, Loader2, Trash2 } from 'lucide-react';

export default function KnowledgeView() {
  const { botId } = useParams();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);
  
  // Preview State
  const [previewFile, setPreviewFile] = useState(null);
  const [previewChunks, setPreviewChunks] = useState([]);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Polling refs
  const pollIntervalRef = useRef(null);
  const previewPollIntervalRef = useRef(null);

  useEffect(() => {
    loadFiles();
    
    // Start polling for file status
    startPolling();
    
    return () => {
      stopPolling();
      stopPreviewPolling();
    };
  }, [botId]);

  // Preview Polling Effect
  useEffect(() => {
    if (previewFile) {
      loadPreview(previewFile.id);
      
      // If file is processing, poll for new chunks
      if (previewFile.status === 'processing' || previewFile.status === 'pending') {
        startPreviewPolling(previewFile.id);
      } else {
        stopPreviewPolling();
      }
    } else {
      stopPreviewPolling();
      setPreviewChunks([]);
    }
  }, [previewFile]);

  const startPolling = () => {
    stopPolling();
    pollIntervalRef.current = setInterval(loadFiles, 3000); // Poll every 3s
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const startPreviewPolling = (fileId) => {
    stopPreviewPolling();
    previewPollIntervalRef.current = setInterval(() => loadPreview(fileId, true), 2000); // Poll chunks every 2s
  };

  const stopPreviewPolling = () => {
    if (previewPollIntervalRef.current) {
      clearInterval(previewPollIntervalRef.current);
      previewPollIntervalRef.current = null;
    }
  };

  const loadFiles = async () => {
    try {
      const response = await getKnowledgeFiles(botId);
      setFiles(response.data);
      
      // Update previewFile status if it's currently open
      if (previewFile) {
        const currentFile = response.data.find(f => f.id === previewFile.id);
        if (currentFile && currentFile.status !== previewFile.status) {
          setPreviewFile(prev => ({ ...prev, status: currentFile.status }));
        }
      }
    } catch (error) {
      console.error('Failed to load knowledge files:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPreview = async (fileId, isPolling = false) => {
    if (!isPolling) setPreviewLoading(true);
    try {
      const response = await getKnowledgePreview(fileId);
      setPreviewChunks(response.data.chunks);
    } catch (error) {
      console.error('Failed to load preview:', error);
    } finally {
      if (!isPolling) setPreviewLoading(false);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await uploadKnowledgeFile(botId, formData);
      setMessage({ type: 'success', text: 'File uploaded successfully. Processing started...' });
      loadFiles();
    } catch (error) {
      console.error('Failed to upload file:', error);
      setMessage({ type: 'error', text: 'Failed to upload file' });
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50';
      case 'processing': return 'text-blue-600 bg-blue-50';
      case 'failed': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const handleDeleteFile = async (fileId) => {
    if (window.confirm('Are you sure you want to delete this file? This action cannot be undone.')) {
      try {
        await deleteKnowledgeFile(fileId);
        setMessage({ type: 'success', text: 'File deleted successfully' });
        loadFiles();
        if (previewFile && previewFile.id === fileId) {
          setPreviewFile(null);
        }
      } catch (error) {
        console.error('Failed to delete file:', error);
        setMessage({ type: 'error', text: 'Failed to delete file' });
      }
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex justify-between items-start mb-10">
        <div>
          <h2 className="text-3xl font-semibold text-white tracking-tight">Knowledge <span className="text-white/60 font-normal">Base</span></h2>
          <p className="text-white/40 mt-1">Manage documents your bot uses for context.</p>
        </div>
        <button 
          onClick={loadFiles}
          className="p-2.5 bg-white/[0.03] border border-white/10 rounded-xl text-white/70 hover:bg-white/[0.06] hover:text-white transition-all duration-200 group"
        >
          <RefreshCw size={18} />
        </button>
      </div>

      {message && (
        <div className={`mb-6 p-4 rounded-xl flex items-center gap-3 ${
          message.type === 'success' ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border border-red-500/20 text-red-400'
        }`}>
          <AlertCircle size={20} />
          <span className="font-medium">{message.text}</span>
        </div>
      )}

      <div className="bg-[#161616]/60 backdrop-blur-xl border border-white/5 rounded-2xl p-6 mb-6">
        <label className={`flex flex-col items-center justify-center w-full h-36 border-2 border-dashed border-white/10 rounded-xl cursor-pointer hover:bg-white/[0.03] transition-colors ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}>
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            {uploading ? (
               <Loader2 className="w-8 h-8 mb-3 text-emerald-400 animate-spin" />
            ) : (
               <Upload className="w-8 h-8 mb-3 text-white/30" />
            )}
            <p className="mb-2 text-sm text-white/60">
              <span className="font-semibold text-emerald-400">{uploading ? 'Uploading...' : 'Click to upload'}</span> or drag and drop
            </p>
            <p className="text-xs text-white/40">PDF, TXT, MD (MAX. 10MB)</p>
          </div>
          <input 
            type="file" 
            className="hidden" 
            onChange={handleUpload}
            disabled={uploading}
            accept=".pdf,.txt,.md"
          />
        </label>
      </div>

      <div className="bg-[#161616]/60 backdrop-blur-xl border border-white/5 rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-white/5">
          <h3 className="font-semibold text-white/80">Uploaded Files</h3>
        </div>
        <div className="divide-y divide-white/5">
          {files.length === 0 ? (
            <div className="p-8 text-center text-white/40">
              No files uploaded yet.
            </div>
          ) : (
            files.map((file) => (
              <div key={file.id} className="p-4 flex items-center justify-between hover:bg-white/[0.03] transition-colors">
                <div className="flex items-center gap-4">
                  <div className="p-2.5 bg-white/5 rounded-lg">
                    <FileText size={20} className="text-white/60" />
                  </div>
                  <div>
                    <h4 className="font-medium text-white/90">{file.file.split('/').pop()}</h4>
                    <div className="flex items-center gap-2 text-sm mt-1">
                       <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColor(file.status)}`}>
                        {file.status}
                      </span>
                      <span className="text-white/40">• {file.chunk_count} chunks</span>
                      {file.processing_error && (
                         <span className="text-red-400 text-xs truncate max-w-[200px]" title={file.processing_error}>• {file.processing_error}</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => setPreviewFile(file)}
                    className="p-2 text-white/50 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg transition-colors flex items-center gap-1.5 text-sm"
                    title="Preview"
                  >
                    <Eye size={16} />
                    <span className="hidden sm:inline">Preview</span>
                  </button>
                  <button 
                    onClick={() => handleDeleteFile(file.id)}
                    className="p-2 text-white/50 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors flex items-center gap-1.5 text-sm"
                    title="Delete"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Preview Modal */}
      {previewFile && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#161616] border border-white/10 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col">
            <div className="p-5 border-b border-white/10 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-lg text-white/90">{previewFile.file.split('/').pop()}</h3>
                <div className="flex items-center gap-2 text-sm mt-1">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColor(previewFile.status)}`}>
                    {previewFile.status}
                  </span>
                  <span className="text-white/40">{previewChunks.length} chunks extracted</span>
                </div>
              </div>
              <button 
                onClick={() => setPreviewFile(null)}
                className="p-2 text-white/50 hover:bg-white/10 rounded-full transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1 bg-black/20">
              {previewLoading ? (
                <div className="flex flex-col items-center justify-center h-64">
                  <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mb-2" />
                  <p className="text-white/40">Loading content...</p>
                </div>
              ) : previewChunks.length === 0 ? (
                <div className="text-center py-12 text-white/40">
                  {previewFile.status === 'processing' || previewFile.status === 'pending' ? (
                     <div className="flex flex-col items-center">
                        <Loader2 className="w-6 h-6 text-emerald-400 animate-spin mb-2" />
                        <p>Waiting for text extraction...</p>
                     </div>
                  ) : (
                    <p>No content extracted.</p>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  {previewChunks.map((chunk) => (
                    <div key={chunk.id} className="bg-[#1c1c1c] p-4 rounded-lg border border-white/10 shadow-sm">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-xs font-mono text-white/30">Chunk #{chunk.index}</span>
                      </div>
                      <p className="text-sm text-white/70 whitespace-pre-wrap font-light">{chunk.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
