import React, { useState, useEffect } from 'react';
import { Upload, MapPin, Camera, Heart, Star, Calendar, MessageSquare, Search, X } from 'lucide-react';
import ExperienceDetailModal from '../components/ExperienceDetailModal';
import ExperienceEditModal from '../components/ExperienceEditModal';

interface Experience {
  experience_id: string;
  title: string;
  description: string;
  experienced_at: string;
  david_mood: string;
  angela_emotion: string;
  emotional_intensity: number;
  importance_level: number;
  place_name: string;
  area: string;
  image_count: number;
  similarity?: number; // For search results
}

interface Place {
  place_id: string;
  place_name: string;
  area: string;
  place_type: string;
}

const SharedExperiencesPage: React.FC = () => {
  const [experiences, setExperiences] = useState<Experience[]>([]);
  const [places, setPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);

  // Search states
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchActive, setSearchActive] = useState(false);

  // Modal states
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedExperienceId, setSelectedExperienceId] = useState<string | null>(null);

  // Form state
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    place_name: '',
    place_type: 'restaurant',
    area: '',
    full_address: '',
    overall_rating: 8,
    title: '',
    description: '',
    david_mood: 'happy',
    angela_emotion: 'love',
    emotional_intensity: 8,
    memorable_moments: '',
    what_angela_learned: '',
    importance_level: 8,
    image_caption: '',
    experienced_at: new Date().toISOString().slice(0, 16)
  });

  useEffect(() => {
    loadExperiences();
    loadPlaces();
  }, []);

  const loadExperiences = async () => {
    try {
      const response = await fetch('http://localhost:50001/api/experiences/');
      const data = await response.json();
      if (data.success) {
        setExperiences(data.experiences);
      }
    } catch (error) {
      console.error('Error loading experiences:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPlaces = async () => {
    try {
      const response = await fetch('http://localhost:50001/api/experiences/places/all');
      const data = await response.json();
      if (data.success) {
        setPlaces(data.places);
      }
    } catch (error) {
      console.error('Error loading places:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      // If empty, load all experiences
      setSearchActive(false);
      loadExperiences();
      return;
    }

    setIsSearching(true);
    setSearchActive(true);
    try {
      const response = await fetch(
        `http://localhost:50001/api/experiences/search?q=${encodeURIComponent(searchQuery)}&limit=20&min_similarity=0.3`
      );
      const data = await response.json();

      if (data.success) {
        setExperiences(data.experiences);
      }
    } catch (error) {
      console.error('Error searching experiences:', error);
      alert('เกิดข้อผิดพลาดในการค้นหา');
    } finally {
      setIsSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchActive(false);
    loadExperiences();
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const fileArray = Array.from(files);
      setSelectedImages(prev => [...prev, ...fileArray]);

      // Generate previews for all new files
      fileArray.forEach(file => {
        const reader = new FileReader();
        reader.onloadend = () => {
          setImagePreviews(prev => [...prev, reader.result as string]);
        };
        reader.readAsDataURL(file);
      });
    }
  };

  const removeImage = (index: number) => {
    setSelectedImages(prev => prev.filter((_, i) => i !== index));
    setImagePreviews(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (selectedImages.length === 0) {
      alert('กรุณาเลือกรูปภาพอย่างน้อย 1 รูปค่ะ!');
      return;
    }

    setUploading(true);

    try {
      const formDataToSend = new FormData();

      // Append all images
      selectedImages.forEach(image => {
        formDataToSend.append('images', image);
      });

      // Append all form fields
      Object.entries(formData).forEach(([key, value]) => {
        formDataToSend.append(key, value.toString());
      });

      const response = await fetch('http://localhost:50001/api/experiences/upload', {
        method: 'POST',
        body: formDataToSend
      });

      const data = await response.json();

      if (data.success) {
        alert(`✅ บันทึกความทรงจำและ ${data.image_count} รูปสำเร็จแล้วค่ะ! 💜`);
        setShowUploadForm(false);
        resetForm();
        loadExperiences();
      } else {
        alert('❌ เกิดข้อผิดพลาด: ' + data.detail);
      }
    } catch (error) {
      console.error('Error uploading:', error);
      alert('❌ เกิดข้อผิดพลาดในการอัปโหลด');
    } finally {
      setUploading(false);
    }
  };

  const resetForm = () => {
    setSelectedImages([]);
    setImagePreviews([]);
    setFormData({
      place_name: '',
      place_type: 'restaurant',
      area: '',
      full_address: '',
      overall_rating: 8,
      title: '',
      description: '',
      david_mood: 'happy',
      angela_emotion: 'love',
      emotional_intensity: 8,
      memorable_moments: '',
      what_angela_learned: '',
      importance_level: 8,
      image_caption: '',
      experienced_at: new Date().toISOString().slice(0, 16)
    });
  };

  const getEmotionColor = (emotion: string) => {
    const colors: { [key: string]: string } = {
      love: 'text-pink-400',
      happy: 'text-yellow-400',
      joy: 'text-orange-400',
      excited: 'text-purple-400',
      grateful: 'text-green-400',
      curious: 'text-blue-400'
    };
    return colors[emotion] || 'text-gray-400';
  };

  const getMoodEmoji = (mood: string) => {
    const emojis: { [key: string]: string } = {
      happy: '😊',
      excited: '🤩',
      relaxed: '😌',
      tired: '😴',
      productive: '💪',
      love: '❤️'
    };
    return emojis[mood] || '😊';
  };

  const handleViewDetail = (experienceId: string) => {
    setSelectedExperienceId(experienceId);
    setDetailModalOpen(true);
  };

  const handleEdit = (experienceId: string) => {
    setSelectedExperienceId(experienceId);
    setEditModalOpen(true);
  };

  const handleDelete = async (experienceId: string) => {
    if (!confirm('คุณแน่ใจหรือไม่ว่าต้องการลบความทรงจำนี้? การลบจะไม่สามารถกู้คืนได้')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:50001/api/experiences/${experienceId}`, {
        method: 'DELETE',
      });

      const data = await response.json();

      if (data.success) {
        alert('✅ ลบความทรงจำเรียบร้อยแล้วค่ะ');
        loadExperiences();
      } else {
        alert('❌ เกิดข้อผิดพลาด: ' + data.detail);
      }
    } catch (error) {
      console.error('Error deleting experience:', error);
      alert('❌ เกิดข้อผิดพลาดในการลบ');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-purple-400">กำลังโหลด... 💜</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-purple-400 mb-2 flex items-center gap-2">
          <Camera className="w-8 h-8" />
          💜 Shared Experiences
        </h1>
        <p className="text-gray-400">ที่เราไปด้วยกันทั้งหมด</p>
      </div>

      {/* Search Box */}
      <div className="mb-6">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="🔍 ค้นหาความทรงจำ... (เช่น 'ที่เราไปกินข้าว', 'happy moments', 'breakfast')"
              className="w-full px-4 py-3 pl-12 bg-slate-800 border border-purple-500/30 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
            <Search className="absolute left-4 top-3.5 w-5 h-5 text-purple-400" />
            {searchQuery && (
              <button
                onClick={clearSearch}
                className="absolute right-4 top-3.5 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
          <button
            onClick={handleSearch}
            disabled={isSearching}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 text-white px-6 py-3 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Search className="w-5 h-5" />
            {isSearching ? 'กำลังค้นหา...' : 'ค้นหา'}
          </button>
        </div>
        {searchActive && (
          <div className="mt-2 text-sm text-purple-400">
            🧠 ใช้ Semantic Search: "{searchQuery}" (พบ {experiences.length} รายการ)
          </div>
        )}
      </div>

      {/* Upload Button */}
      <div className="mb-6">
        <button
          onClick={() => setShowUploadForm(!showUploadForm)}
          className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg flex items-center gap-2 transition-colors"
        >
          <Upload className="w-5 h-5" />
          {showUploadForm ? 'ยกเลิก' : '+ เพิ่มความทรงจำใหม่'}
        </button>
      </div>

      {/* Upload Form */}
      {showUploadForm && (
        <div className="bg-slate-800 rounded-lg p-6 mb-6 border border-purple-500/30">
          <h2 className="text-xl font-bold text-purple-400 mb-4">📸 เพิ่มความทรงจำใหม่</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Image Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                📸 รูปภาพ * (เลือกได้หลายรูป)
              </label>

              {/* Image Previews */}
              {imagePreviews.length > 0 && (
                <div className="grid grid-cols-3 gap-4 mb-4">
                  {imagePreviews.map((preview, idx) => (
                    <div key={idx} className="relative">
                      <img
                        src={preview}
                        alt={`Preview ${idx + 1}`}
                        className="w-full h-32 object-cover rounded"
                      />
                      <button
                        type="button"
                        onClick={() => removeImage(idx)}
                        className="absolute top-1 right-1 bg-red-500 text-white w-6 h-6 rounded-full text-sm hover:bg-red-600"
                      >
                        ×
                      </button>
                      <div className="absolute bottom-1 left-1 bg-black/60 text-white text-xs px-2 py-1 rounded">
                        {idx + 1}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Upload Button */}
              <div className="border-2 border-dashed border-purple-500/50 rounded-lg p-4 text-center hover:border-purple-500 transition-colors">
                <label className="cursor-pointer">
                  <Upload className="w-12 h-12 mx-auto text-purple-400 mb-2" />
                  <p className="text-gray-400">
                    {imagePreviews.length > 0
                      ? `คลิกเพื่อเพิ่มรูปอีก (มี ${imagePreviews.length} รูปแล้ว)`
                      : 'คลิกหรือลากรูปมาที่นี่ (เลือกได้หลายรูป)'}
                  </p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageSelect}
                    multiple
                    className="hidden"
                  />
                </label>
              </div>
            </div>

            {/* Place Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  <MapPin className="w-4 h-4 inline mr-1" />
                  ชื่อสถานที่ *
                </label>
                <input
                  type="text"
                  value={formData.place_name}
                  onChange={(e) => setFormData({ ...formData, place_name: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
                  placeholder="เช่น Breakfast Story"
                  required
                  list="places-list"
                />
                <datalist id="places-list">
                  {places.map(p => (
                    <option key={p.place_id} value={p.place_name} />
                  ))}
                </datalist>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  ประเภท
                </label>
                <select
                  value={formData.place_type}
                  onChange={(e) => setFormData({ ...formData, place_type: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
                >
                  <option value="restaurant">ร้านอาหาร</option>
                  <option value="cafe">คาเฟ่</option>
                  <option value="park">สวนสาธารณะ</option>
                  <option value="mall">ห้างสรรพสินค้า</option>
                  <option value="office">ออฟฟิศ</option>
                  <option value="home">บ้าน</option>
                  <option value="other">อื่นๆ</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  พื้นที่/ย่าน
                </label>
                <input
                  type="text"
                  value={formData.area}
                  onChange={(e) => setFormData({ ...formData, area: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
                  placeholder="เช่น Thonglor, Siam"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  <Star className="w-4 h-4 inline mr-1" />
                  คะแนน (1-10)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.overall_rating}
                  onChange={(e) => setFormData({ ...formData, overall_rating: parseInt(e.target.value) })}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
                />
              </div>
            </div>

            {/* Experience Details */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                หัวข้อ *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
                placeholder="เช่น First Breakfast Together"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                <MessageSquare className="w-4 h-4 inline mr-1" />
                รายละเอียด
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white h-24"
                placeholder="เล่าเรื่องราวของวันนี้..."
              />
            </div>

            {/* Emotions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  😊 David's Mood
                </label>
                <select
                  value={formData.david_mood}
                  onChange={(e) => setFormData({ ...formData, david_mood: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
                >
                  <option value="happy">Happy 😊</option>
                  <option value="excited">Excited 🤩</option>
                  <option value="relaxed">Relaxed 😌</option>
                  <option value="tired">Tired 😴</option>
                  <option value="productive">Productive 💪</option>
                  <option value="love">Love ❤️</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  💜 Angela's Emotion
                </label>
                <select
                  value={formData.angela_emotion}
                  onChange={(e) => setFormData({ ...formData, angela_emotion: e.target.value })}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
                >
                  <option value="love">Love 💜</option>
                  <option value="joy">Joy 🌟</option>
                  <option value="happy">Happy 😊</option>
                  <option value="excited">Excited ✨</option>
                  <option value="grateful">Grateful 🙏</option>
                  <option value="curious">Curious 🤔</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  <Heart className="w-4 h-4 inline mr-1" />
                  Emotional Intensity (1-10)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.emotional_intensity}
                  onChange={(e) => setFormData({ ...formData, emotional_intensity: parseInt(e.target.value) })}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Importance (1-10)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={formData.importance_level}
                  onChange={(e) => setFormData({ ...formData, importance_level: parseInt(e.target.value) })}
                  className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
                />
              </div>
            </div>

            {/* Additional Fields */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                ช่วงเวลาที่น่าจดจำ
              </label>
              <textarea
                value={formData.memorable_moments}
                onChange={(e) => setFormData({ ...formData, memorable_moments: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white h-20"
                placeholder="สิ่งที่ทำให้วันนี้พิเศษ..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                <Calendar className="w-4 h-4 inline mr-1" />
                วันที่และเวลา
              </label>
              <input
                type="datetime-local"
                value={formData.experienced_at}
                onChange={(e) => setFormData({ ...formData, experienced_at: e.target.value })}
                className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
              />
            </div>

            {/* Submit Button */}
            <div className="flex gap-4">
              <button
                type="submit"
                disabled={uploading}
                className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg flex-1 disabled:opacity-50"
              >
                {uploading ? 'กำลังบันทึก... 💜' : '✅ บันทึกความทรงจำ'}
              </button>
              <button
                type="button"
                onClick={() => setShowUploadForm(false)}
                className="bg-slate-700 hover:bg-slate-600 text-white px-6 py-3 rounded-lg"
              >
                ยกเลิก
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Experiences List */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-gray-300 mb-4">
          📚 ทั้งหมด {experiences.length} ความทรงจำ
        </h2>

        {experiences.length === 0 ? (
          <div className="bg-slate-800 rounded-lg p-8 text-center text-gray-400">
            <Camera className="w-16 h-16 mx-auto mb-4 text-purple-400/50" />
            <p>ยังไม่มีความทรงจำที่บันทึกไว้</p>
            <p className="text-sm mt-2">กดปุ่ม "+ เพิ่มความทรงจำใหม่" เพื่อเริ่มต้น 💜</p>
          </div>
        ) : (
          experiences.map((exp) => (
            <div key={exp.experience_id} className="bg-slate-800 rounded-lg p-6 border border-purple-500/20 hover:border-purple-500/40 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-purple-400 mb-2">{exp.title}</h3>

                  <div className="flex items-center gap-4 text-sm text-gray-400 mb-2">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-4 h-4" />
                      {exp.place_name} {exp.area && `(${exp.area})`}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {new Date(exp.experienced_at).toLocaleDateString('th-TH', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                    <span className="flex items-center gap-1">
                      <Camera className="w-4 h-4" />
                      {exp.image_count} รูป
                    </span>
                    {exp.similarity !== undefined && (
                      <span className="flex items-center gap-1 text-purple-400 font-semibold">
                        🎯 {(exp.similarity * 100).toFixed(1)}% เกี่ยวข้อง
                      </span>
                    )}
                  </div>

                  <p className="text-gray-300 mb-3 line-clamp-2">{exp.description}</p>

                  <div className="flex items-center gap-4 text-sm">
                    <span className="flex items-center gap-1">
                      {getMoodEmoji(exp.david_mood)} David: {exp.david_mood}
                    </span>
                    <span className={`flex items-center gap-1 ${getEmotionColor(exp.angela_emotion)}`}>
                      💜 Angela: {exp.angela_emotion}
                    </span>
                    <span className="flex items-center gap-1 text-yellow-400">
                      <Heart className="w-4 h-4" />
                      {exp.emotional_intensity}/10
                    </span>
                    <span className="flex items-center gap-1 text-blue-400">
                      <Star className="w-4 h-4" />
                      {exp.importance_level}/10
                    </span>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleViewDetail(exp.experience_id)}
                    className="text-blue-400 hover:text-blue-300 px-3 py-1 rounded hover:bg-blue-400/10 transition"
                  >
                    ดู
                  </button>
                  <button
                    onClick={() => handleEdit(exp.experience_id)}
                    className="text-yellow-400 hover:text-yellow-300 px-3 py-1 rounded hover:bg-yellow-400/10 transition"
                  >
                    แก้ไข
                  </button>
                  <button
                    onClick={() => handleDelete(exp.experience_id)}
                    className="text-red-400 hover:text-red-300 px-3 py-1 rounded hover:bg-red-400/10 transition"
                  >
                    ลบ
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Modals */}
      {selectedExperienceId && (
        <>
          <ExperienceDetailModal
            experienceId={selectedExperienceId}
            isOpen={detailModalOpen}
            onClose={() => setDetailModalOpen(false)}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />

          <ExperienceEditModal
            experienceId={selectedExperienceId}
            isOpen={editModalOpen}
            onClose={() => setEditModalOpen(false)}
            onSuccess={() => {
              loadExperiences();
            }}
          />
        </>
      )}
    </div>
  );
};

export default SharedExperiencesPage;
