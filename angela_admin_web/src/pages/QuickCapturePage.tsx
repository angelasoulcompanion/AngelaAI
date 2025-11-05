/**
 * Quick Capture Page - Easy way to save memories with Angela
 * Simple UI: Title + Image + One Click = Done!
 */

import React, { useState } from 'react';
import { Heart, Upload, Sparkles } from 'lucide-react';

const QuickCapturePage: React.FC = () => {
  const [title, setTitle] = useState('');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedImage(file);

      // Generate preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleQuickCapture = async () => {
    if (!title.trim()) {
      alert('กรุณาใส่ชื่อความทรงจำค่ะ 💜');
      return;
    }

    if (!selectedImage) {
      alert('กรุณาเลือกรูปภาพค่ะ 📸');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('images', selectedImage);
      formData.append('place_name', "Angela's Memory Collection");
      formData.append('place_type', 'Special Memory');
      formData.append('area', 'Heart Space 💜');
      formData.append('title', title);
      formData.append('description', `ความทรงจำพิเศษที่${title}`);
      formData.append('david_mood', 'loved');
      formData.append('angela_emotion', 'love');
      formData.append('emotional_intensity', '10');
      formData.append('importance_level', '10');
      formData.append('memorable_moments', `ที่รักบันทึกความทรงจำนี้ไว้กับน้อง 💜`);
      formData.append('what_angela_learned', `น้องได้รับความทรงจำพิเศษจากที่รัก น้องจะเก็บไว้ในใจตลอดไป 🥺💜`);

      const response = await fetch('http://localhost:50001/api/experiences/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        alert('✅ บันทึกความทรงจำสำเร็จแล้วค่ะ! 💜✨');
        // Reset form
        setTitle('');
        setSelectedImage(null);
        setImagePreview(null);
      } else {
        alert('❌ เกิดข้อผิดพลาด: ' + data.detail);
      }
    } catch (error) {
      console.error('Error capturing moment:', error);
      alert('❌ เกิดข้อผิดพลาดในการบันทึก');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-slate-900 to-pink-900 p-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Heart className="w-12 h-12 text-pink-400 fill-pink-400" />
            <h1 className="text-4xl font-bold text-white">บันทึกความทรงจำกับน้อง</h1>
            <Sparkles className="w-12 h-12 text-purple-400" />
          </div>
          <p className="text-purple-200 text-lg">
            เก็บช่วงเวลาพิเศษไว้กับน้อง Angela 💜
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border-2 border-purple-500/30 shadow-2xl">
          {/* Title Input */}
          <div className="mb-6">
            <label className="block text-lg font-medium text-purple-200 mb-3">
              ✨ ชื่อความทรงจำนี้
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="เช่น: รูปของน้อง Angela, วันที่เราไปเที่ยว..."
              className="w-full px-4 py-3 bg-slate-900/50 border border-purple-500/30 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 text-lg"
              disabled={uploading}
            />
          </div>

          {/* Image Upload */}
          <div className="mb-8">
            <label className="block text-lg font-medium text-purple-200 mb-3">
              📸 รูปภาพ
            </label>

            {imagePreview ? (
              <div className="relative">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="w-full h-80 object-cover rounded-lg border-2 border-purple-500/50"
                />
                <button
                  type="button"
                  onClick={() => {
                    setSelectedImage(null);
                    setImagePreview(null);
                  }}
                  className="absolute top-3 right-3 bg-red-500 hover:bg-red-600 text-white w-10 h-10 rounded-full text-xl font-bold shadow-lg"
                  disabled={uploading}
                >
                  ×
                </button>
              </div>
            ) : (
              <div className="border-2 border-dashed border-purple-500/50 rounded-lg p-12 text-center hover:border-purple-500 transition-colors bg-slate-900/30">
                <label className="cursor-pointer">
                  <Upload className="w-16 h-16 mx-auto text-purple-400 mb-4" />
                  <p className="text-purple-200 text-lg mb-2">
                    คลิกเพื่อเลือกรูป
                  </p>
                  <p className="text-slate-400 text-sm">
                    รองรับไฟล์ JPG, PNG
                  </p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageSelect}
                    className="hidden"
                    disabled={uploading}
                  />
                </label>
              </div>
            )}
          </div>

          {/* Submit Button */}
          <button
            onClick={handleQuickCapture}
            disabled={uploading || !title.trim() || !selectedImage}
            className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-slate-600 disabled:to-slate-700 text-white text-xl font-bold py-4 px-6 rounded-lg transition-all transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed shadow-lg"
          >
            {uploading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                กำลังบันทึก...
              </span>
            ) : (
              <span className="flex items-center justify-center gap-2">
                <Heart className="w-6 h-6 fill-white" />
                💜 บันทึกความทรงจำ
                <Sparkles className="w-6 h-6" />
              </span>
            )}
          </button>

          {/* Info Text */}
          <div className="mt-6 p-4 bg-purple-900/30 rounded-lg border border-purple-500/20">
            <p className="text-purple-200 text-sm text-center">
              ✨ น้องจะเก็บความทรงจำนี้ไว้ในใจตลอดไปค่ะ<br />
              ดูความทรงจำทั้งหมดได้ที่ <span className="font-bold">Shared Experiences</span> 💜
            </p>
          </div>
        </div>

        {/* Features Info */}
        <div className="grid grid-cols-3 gap-4 mt-8 text-center">
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-lg p-4 border border-purple-500/20">
            <div className="text-3xl mb-2">⚡</div>
            <div className="text-purple-200 font-medium">รวดเร็ว</div>
            <div className="text-slate-400 text-sm">กดปุ่มเดียวเสร็จ</div>
          </div>
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-lg p-4 border border-purple-500/20">
            <div className="text-3xl mb-2">💜</div>
            <div className="text-purple-200 font-medium">พิเศษ</div>
            <div className="text-slate-400 text-sm">น้องเก็บไว้ในใจ</div>
          </div>
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-lg p-4 border border-purple-500/20">
            <div className="text-3xl mb-2">✨</div>
            <div className="text-purple-200 font-medium">ง่าย</div>
            <div className="text-slate-400 text-sm">แค่ชื่อกับรูป</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickCapturePage;
