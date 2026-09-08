import os

with open('frontend/src/views/ANPRView.jsx', 'r') as f:
    content = f.read()

# 1. Update imports to include Upload
content = content.replace("import { Cpu, Play, Image, Video, RefreshCw, CheckCircle2, AlertCircle, Clock, Zap, ChevronDown, ChevronUp } from 'lucide-react';", 
                          "import { Cpu, Play, Image, Video, RefreshCw, CheckCircle2, AlertCircle, Clock, Zap, ChevronDown, ChevronUp, Upload, X } from 'lucide-react';")

# 2. Add apiPostFormData
api_form_data = """
async function apiPostFormData(path, formData) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}
"""
content = content.replace("async function apiGet", api_form_data + "\nasync function apiGet")

# 3. Add inputSource state
content = content.replace("const [useVideo, setUseVideo] = useState(true);", 
                          "const [inputSource, setInputSource] = useState('demo-video');\n  const [selectedFile, setSelectedFile] = useState(null);\n  const [videoUrl, setVideoUrl] = useState(null);\n")

# 4. Update runTest
old_run_test = """
  const runTest = async () => {
    try {
      setGenerating(true);
      setTestResult(null);
      setTestError(null);
      const result = await apiPost('/anpr/generate-test', {
        generate_video: useVideo,
        run_anpr: true,
        camera_id: cameraId,
        noise_level: noiseLevel,
        plates: ['TS09AB1234', 'DL01CZ4567', 'KA05MH8899', 'MH12TR3321'],
      });
      setTestResult(result);
    } catch (err) {
      setTestError(`ANPR pipeline error: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };
"""

new_run_test = """
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setSelectedFile(file);
    if (videoUrl) URL.revokeObjectURL(videoUrl);
    setVideoUrl(URL.createObjectURL(file));
  };

  const runTest = async () => {
    try {
      setGenerating(true);
      setTestResult(null);
      setTestError(null);
      
      let result;
      if (inputSource === 'upload-video') {
        if (!selectedFile) throw new Error("Please select a video file first.");
        const formData = new FormData();
        formData.append('video', selectedFile);
        formData.append('camera_id', cameraId);
        formData.append('min_confidence', minConf);
        formData.append('frame_sample_interval', 30);
        result = await apiPostFormData('/anpr/upload-video', formData);
      } else {
        result = await apiPost('/anpr/generate-test', {
          generate_video: inputSource === 'demo-video',
          run_anpr: true,
          camera_id: cameraId,
          noise_level: noiseLevel,
          plates: ['TS09AB1234', 'DL01CZ4567', 'KA05MH8899', 'MH12TR3321'],
        });
      }
      setTestResult(result);
    } catch (err) {
      setTestError(`ANPR pipeline error: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };
"""
content = content.replace(old_run_test.strip(), new_run_test.strip())

# 5. Update Input Mode UI
old_input_mode = """
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">Input Mode</label>
            <div className="flex gap-2">
              <button
                onClick={() => setUseVideo(true)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold border transition ${
                  useVideo ? 'bg-sky-500 text-white border-sky-400' : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
              >
                <Video className="w-3.5 h-3.5" /> Video
              </button>
              <button
                onClick={() => setUseVideo(false)}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold border transition ${
                  !useVideo ? 'bg-sky-500 text-white border-sky-400' : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
              >
                <Image className="w-3.5 h-3.5" /> Images
              </button>
            </div>
          </div>
"""

new_input_mode = """
          <div className="col-span-1 sm:col-span-2 lg:col-span-2">
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">Input Source</label>
            <div className="flex gap-2">
              <button
                onClick={() => setInputSource('demo-video')}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold border transition ${
                  inputSource === 'demo-video' ? 'bg-sky-500 text-white border-sky-400' : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
              >
                <Video className="w-3.5 h-3.5" /> Demo Video
              </button>
              <button
                onClick={() => setInputSource('demo-images')}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold border transition ${
                  inputSource === 'demo-images' ? 'bg-sky-500 text-white border-sky-400' : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
              >
                <Image className="w-3.5 h-3.5" /> Demo Images
              </button>
              <button
                onClick={() => setInputSource('upload-video')}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold border transition ${
                  inputSource === 'upload-video' ? 'bg-sky-500 text-white border-sky-400' : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
              >
                <Upload className="w-3.5 h-3.5" /> Upload Video
              </button>
            </div>
          </div>
"""
content = content.replace(old_input_mode.strip(), new_input_mode.strip())

# 6. Disable noise level and handle file upload UI
old_noise = """
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">Image Noise</label>
            <select
              value={noiseLevel}
              onChange={e => setNoiseLevel(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-sky-500"
            >
              <option value="low">Low (Clear)</option>
              <option value="medium">Medium (Blurred)</option>
              <option value="high">High (Compressed)</option>
            </select>
          </div>
"""
new_noise = """
          <div>
            <label className="block text-xs text-slate-400 mb-1.5 font-medium">Image Noise (Demo Only)</label>
            <select
              disabled={inputSource === 'upload-video'}
              value={noiseLevel}
              onChange={e => setNoiseLevel(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-sky-500 disabled:opacity-50"
            >
              <option value="low">Low (Clear)</option>
              <option value="medium">Medium (Blurred)</option>
              <option value="high">High (Compressed)</option>
            </select>
          </div>
"""
content = content.replace(old_noise.strip(), new_noise.strip())

file_upload_ui = """
        {inputSource === 'upload-video' && (
          <div className="pt-4 border-t border-slate-800">
            <label className="block text-xs text-slate-400 mb-2 font-medium">Select Local Video File (.mp4, .avi, .mov, .mkv)</label>
            <div className="flex items-center gap-4">
              <input
                type="file"
                accept=".mp4,.avi,.mov,.mkv"
                onChange={handleFileSelect}
                className="hidden"
                id="video-upload"
              />
              <label
                htmlFor="video-upload"
                className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold bg-slate-800 text-slate-200 border border-slate-700 hover:border-sky-500 hover:text-sky-400 transition"
              >
                <Upload className="w-4 h-4" />
                Choose File
              </label>
              {selectedFile && (
                <div className="flex items-center gap-3 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                  <span className="text-sm text-sky-300 font-mono">{selectedFile.name}</span>
                  <span className="text-xs text-slate-500">{(selectedFile.size / (1024 * 1024)).toFixed(1)} MB</span>
                  <button onClick={() => { setSelectedFile(null); setVideoUrl(null); }} className="text-slate-500 hover:text-red-400">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
"""

content = content.replace('<div className="pt-2 border-t border-slate-800 flex items-center justify-between gap-4">', file_upload_ui + '\n        <div className="pt-2 border-t border-slate-800 flex items-center justify-between gap-4">')

# 7. Update text description
old_text = "Generates synthetic license plate images/video → runs full plate detection and OCR → stores real detections (marked"
new_text = "Runs full plate detection and OCR on the selected input → stores real detections (marked"
content = content.replace(old_text, new_text)

# Write to file
with open('frontend/src/views/ANPRView.jsx', 'w') as f:
    f.write(content)
