'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, Paperclip, Plus, Menu, X, StopCircle, Loader2, ThumbsUp, ThumbsDown } from 'lucide-react';
import axios from 'axios';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: { name: string; type: string; url: string; size?: number }[];
  solution?: any;
}

interface Session {
  session_id: string;
  created_at: string;
  status: string;
  upload_type: 'image' | 'audio' | 'text';
  has_solution: boolean;
  problem_type?: string;
}

export default function JEEMathChatbot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([]);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/v1/session?page=1&page_size=50`);
      if (response.data.success) {
        setSessions(response.data.sessions);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() && uploadedFiles.length === 0) return;

    // Create user message
    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
      attachments: uploadedFiles.length > 0 ? [...uploadedFiles] : undefined
    };

    setMessages(prev => [...prev, newMessage]);
    const currentInput = input;
    setInput('');
    const currentFiles = [...uploadedFiles];
    setUploadedFiles([]);
    setIsLoading(true);

    try {
      let sessionId = currentSessionId;

      // Step 1: Upload content if no session exists
      if (!sessionId) {
        // Upload image if attached
        if (currentFiles.length > 0 && currentFiles[0].type.startsWith('image/')) {
          const formData = new FormData();
          formData.append('file', currentFiles[0].file);

          const uploadRes = await axios.post(`${API_URL}/api/v1/upload/image`, formData);
          sessionId = uploadRes.data.session_id;
        } 
        // Upload text
        else if (currentInput.trim()) {
          const uploadRes = await axios.post(`${API_URL}/api/v1/upload/text`, {
            text: currentInput
          });
          sessionId = uploadRes.data.session_id;
        }

        if (sessionId) {
          setCurrentSessionId(sessionId);
        }
      }

      // Step 2: Solve the problem
      if (sessionId) {
        const solveRes = await axios.post(`${API_URL}/api/v1/solve`, {
          session_id: sessionId,
          require_steps: true,
          problem_type: 'auto'
        });

        if (solveRes.data.success && solveRes.data.solution) {
          const solution = solveRes.data.solution;
          
          // Format solution as text
          let solutionText = `**Answer:** ${solution.answer}\n\n`;
          
          if (solution.steps && solution.steps.length > 0) {
            solutionText += '**Solution Steps:**\n\n';
            solution.steps.forEach((step: any) => {
              solutionText += `**Step ${step.step_number}: ${step.title}**\n`;
              solutionText += `${step.description}\n`;
              if (step.formula) {
                solutionText += `Formula: ${step.formula}\n`;
              }
              if (step.explanation) {
                solutionText += `${step.explanation}\n`;
              }
              solutionText += '\n';
            });
          }

          const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: solutionText,
            timestamp: new Date(),
            solution: solution
          };
          
          setMessages(prev => [...prev, aiMessage]);
          await loadSessions(); // Refresh sessions list
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Determine upload endpoint based on file type
     let uploadEndpoint = `${API_URL}/api/v1/upload/image`;
      if (file.type.startsWith('audio/')) {
        uploadEndpoint = `${API_URL}/api/v1/upload/audio`;
        formData.append('transcribe', 'true');
      }

      const response = await axios.post(uploadEndpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.success) {
        const attachment = {
          name: file.name,
          type: file.type,
          url: response.data.file_url,
          size: file.size,
          file: file
        };
        
        setUploadedFiles(prev => [...prev, attachment]);
        setCurrentSessionId(response.data.session_id);

        // If audio was transcribed, set the input
        if (response.data.transcription) {
          setInput(response.data.transcription);
        }
      }
    } catch (error) {
      console.error('Failed to upload file:', error);
      alert('Failed to upload file. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;

        const audioChunks: Blob[] = [];
        mediaRecorder.ondataavailable = (event) => {
          audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
          stream.getTracks().forEach(track => track.stop());

          // Upload audio with transcription
          const formData = new FormData();
          formData.append('file', audioBlob, 'recording.wav');
          formData.append('transcribe', 'true');

          setIsLoading(true);
          try {
            const response = await axios.post(`${API_URL}/api/v1/upload/audio`, formData);
            if (response.data.success) {
              setInput(response.data.transcription || '');
              setCurrentSessionId(response.data.session_id);
            }
          } catch (error) {
            console.error('Failed to transcribe audio:', error);
            alert('Failed to transcribe audio. Please try again.');
          } finally {
            setIsLoading(false);
          }
        };

        mediaRecorder.start();
        setIsRecording(true);
      } catch (error) {
        console.error('Error accessing microphone:', error);
        alert('Could not access microphone. Please check permissions.');
      }
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setCurrentSessionId(null);
    setUploadedFiles([]);
  };

  const handleSelectSession = async (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setIsLoading(true);

    try {
      // Get session details
      const response = await axios.get(`${API_URL}/api/v1/session/${sessionId}`);
      if (response.data.success) {
        const session = response.data.session;
        const newMessages: Message[] = [];

        // Add user message based on upload type
        if (session.upload_data) {
          const userMsg: Message = {
            id: '1',
            role: 'user',
            content: session.upload_data.content || 'Uploaded problem',
            timestamp: new Date(session.created_at),
            attachments: session.upload_data.url ? [{
              name: 'uploaded-file',
              type: session.upload_data.type,
              url: session.upload_data.url
            }] : undefined
          };
          newMessages.push(userMsg);
        }

        // Add AI solution if exists
        if (session.solution) {
          const solution = session.solution;
          let solutionText = `**Answer:** ${solution.answer}\n\n`;
          
          if (solution.steps && solution.steps.length > 0) {
            solutionText += '**Solution Steps:**\n\n';
            solution.steps.forEach((step: any) => {
              solutionText += `**Step ${step.step_number}: ${step.title}**\n`;
              solutionText += `${step.description}\n`;
              if (step.formula) {
                solutionText += `Formula: ${step.formula}\n`;
              }
              solutionText += '\n';
            });
          }

          const aiMsg: Message = {
            id: '2',
            role: 'assistant',
            content: solutionText,
            timestamp: new Date(session.updated_at),
            solution: solution
          };
          newMessages.push(aiMsg);
        }
 
        setMessages(newMessages);
      }
    } catch (error) {
      console.error('Failed to load session:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = async (isCorrect: boolean, rating: number) => {
    if (!currentSessionId) return;

    try {
        await axios.post(`${API_URL}/api/v1/solve/${currentSessionId}/feedback`, {
        rating,
        is_correct: isCorrect,
        comments: isCorrect ? 'Correct solution' : 'Incorrect solution'
      });
      
      alert('Feedback submitted successfully!');
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const removeUploadedFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="flex h-screen bg-black text-white">
      {/* Sidebar */}
      <div
        className={`${
          isSidebarOpen ? 'w-64' : 'w-0'
        } transition-all duration-300 bg-zinc-950 border-r border-zinc-800 flex flex-col overflow-hidden`}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-zinc-800">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 px-4 py-3 bg-zinc-900 hover:bg-zinc-800 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span className="text-sm font-medium">New Question</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider px-3 mb-2">
            Recent Sessions
          </h3>
          {sessions.length === 0 ? (
            <div className="px-3 py-8 text-center text-sm text-zinc-600">
              No sessions yet
            </div>
          ) : (
            sessions.map((session) => (
              <button
                key={session.session_id}
                onClick={() => handleSelectSession(session.session_id)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  currentSessionId === session.session_id
                    ? 'bg-zinc-800'
                    : 'hover:bg-zinc-900'
                }`}
              >
                <div className="flex items-center gap-2 text-sm font-medium truncate">
                  <span className="text-zinc-400 text-xs">
                    {session.upload_type === 'image' ? '🖼️' : 
                     session.upload_type === 'audio' ? '🎤' : '📝'}
                  </span>
                  {session.problem_type || 'Math Problem'}
                </div>
                <div className="text-xs text-zinc-500 mt-1">
                  {session.status} • {new Date(session.created_at).toLocaleDateString()}
                </div>
              </button>
            ))
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-zinc-800">
          <div className="text-xs text-zinc-500">JEE Math AI Assistant</div>
          <div className="text-xs text-zinc-600 mt-1">API v1.0.0</div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-black">
        {/* Header */}
        <div className="h-16 border-b border-zinc-800 flex items-center px-6 gap-4">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 hover:bg-zinc-900 rounded-lg transition-colors"
          >
            {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div>
            <h1 className="text-lg font-semibold">JEE Mathematics Assistant</h1>
            {currentSessionId && (
              <p className="text-xs text-zinc-500">Session: {currentSessionId.slice(0, 8)}...</p>
            )}
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center max-w-md">
                <div className="w-16 h-16 bg-zinc-900 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">📐</span>
                </div>
                <h2 className="text-xl font-semibold mb-2">Welcome to JEE Math AI</h2>
                <p className="text-zinc-500 text-sm mb-4">
                  Upload a problem image, type your question, or use voice input to get
                  step-by-step solutions
                </p>
                <div className="flex flex-wrap gap-2 justify-center text-xs">
                  <span className="px-3 py-1 bg-zinc-900 rounded-full">📸 Images</span>
                  <span className="px-3 py-1 bg-zinc-900 rounded-full">🎤 Voice</span>
                  <span className="px-3 py-1 bg-zinc-900 rounded-full">📝 Text</span>
                  <span className="px-3 py-1 bg-zinc-900 rounded-full">🧮 Step-by-step</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-zinc-800'
                        : 'bg-zinc-900 border border-zinc-800'
                    }`}
                  >
                    {message.attachments && message.attachments.length > 0 && (
                      <div className="mb-2 space-y-2">
                        {message.attachments.map((attachment, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-2 p-2 bg-zinc-950 rounded-lg text-sm"
                          >
                            <Paperclip className="w-4 h-4 text-zinc-500" />
                            <span className="truncate">{attachment.name}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">
                      {message.content}
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="text-xs text-zinc-600">
                        {message.timestamp.toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>
                      {message.role === 'assistant' && message.solution && (
                        <div className="flex gap-1 ml-auto">
                          <button
                            onClick={() => handleFeedback(true, 5)}
                            className="p-1 hover:bg-zinc-800 rounded transition-colors"
                            title="Correct solution"
                          >
                            <ThumbsUp className="w-3 h-3 text-zinc-500 hover:text-green-500" />
                          </button>
                          <button
                            onClick={() => handleFeedback(false, 1)}
                            className="p-1 hover:bg-zinc-800 rounded transition-colors"
                            title="Incorrect solution"
                          >
                            <ThumbsDown className="w-3 h-3 text-zinc-500 hover:text-red-500" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-zinc-900 border border-zinc-800 rounded-2xl px-4 py-3">
                    <Loader2 className="w-5 h-5 animate-spin text-zinc-500" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-zinc-800 p-6">
          <div className="max-w-3xl mx-auto">
            {uploadedFiles.length > 0 && (
              <div className="mb-3 flex flex-wrap gap-2">
                {uploadedFiles.map((file, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-2 px-3 py-2 bg-zinc-900 rounded-lg text-sm"
                  >
                    <Paperclip className="w-4 h-4" />
                    <span className="truncate max-w-[200px]">{file.name}</span>
                    <button
                      onClick={() => removeUploadedFile(idx)}
                      className="text-zinc-500 hover:text-white"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="flex items-end gap-3">
              {/* File Upload Button */}
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileUpload}
                accept="image/*,.pdf,.doc,.docx"
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
                className="p-3 bg-zinc-900 hover:bg-zinc-800 rounded-xl transition-colors disabled:opacity-50"
                title="Upload file"
              >
                <Paperclip className="w-5 h-5" />
              </button>

              {/* Text Input */}
              <div className="flex-1 bg-zinc-900 rounded-xl border border-zinc-800 focus-within:border-zinc-700 transition-colors">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Ask a JEE Math question..."
                  className="w-full bg-transparent px-4 py-3 text-sm resize-none outline-none max-h-32"
                  rows={1}
                  disabled={isLoading}
                />
              </div>

              {/* Voice Input Button */}
              <button
                onClick={toggleRecording}
                disabled={isLoading}
                className={`p-3 rounded-xl transition-all disabled:opacity-50 ${
                  isRecording
                    ? 'bg-red-600 hover:bg-red-700 animate-pulse'
                    : 'bg-zinc-900 hover:bg-zinc-800'
                }`}
                title={isRecording ? 'Stop recording' : 'Start voice input'}
              >
                {isRecording ? (
                  <StopCircle className="w-5 h-5" />
                ) : (
                  <Mic className="w-5 h-5" />
                )}
              </button>

              {/* Send Button */}
              <button
                onClick={handleSend}
                disabled={(!input.trim() && uploadedFiles.length === 0) || isLoading}
                className="p-3 bg-white text-black hover:bg-zinc-200 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="Send message"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>

            {isRecording && (
              <div className="mt-2 text-xs text-zinc-500 flex items-center gap-2">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                Recording... Click the stop button when done
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}