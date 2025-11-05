/**
 * Experience Edit Modal Component
 * Edit existing experience details
 */

import React, { useEffect, useState } from 'react';

interface FormData {
  title: string;
  description: string;
  david_mood: string;
  angela_emotion: string;
  emotional_intensity: number;
  importance_level: number;
  memorable_moments: string;
  what_angela_learned: string;
  experienced_at: string;
}

interface Image {
  image_id: string;
  original_filename: string;
  image_caption?: string;
}

interface ExperienceEditModalProps {
  experienceId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const ExperienceEditModal: React.FC<ExperienceEditModalProps> = ({
  experienceId,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<FormData>({
    title: '',
    description: '',
    david_mood: 'happy',
    angela_emotion: 'love',
    emotional_intensity: 8,
    importance_level: 8,
    memorable_moments: '',
    what_angela_learned: '',
    experienced_at: new Date().toISOString().slice(0, 16),
  });
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [existingImages, setExistingImages] = useState<Image[]>([]);
  const [newImages, setNewImages] = useState<File[]>([]);
  const [newImagePreviews, setNewImagePreviews] = useState<string[]>([]);
  const [uploadingImages, setUploadingImages] = useState(false);

  useEffect(() => {
    if (isOpen && experienceId) {
      // Clear new image state when opening/switching experiences
      setNewImages([]);
      setNewImagePreviews([]);
      fetchExperience();
    }
  }, [isOpen, experienceId]);

  const fetchExperience = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:50001/api/experiences/${experienceId}`);
      const data = await response.json();

      if (data.success) {
        const exp = data.experience;
        setFormData({
          title: exp.title || '',
          description: exp.description || '',
          david_mood: exp.david_mood || 'happy',
          angela_emotion: exp.angela_emotion || 'love',
          emotional_intensity: exp.emotional_intensity || 8,
          importance_level: exp.importance_level || 8,
          memorable_moments: exp.memorable_moments || '',
          what_angela_learned: exp.what_angela_learned || '',
          experienced_at: exp.experienced_at ? new Date(exp.experienced_at).toISOString().slice(0, 16) : new Date().toISOString().slice(0, 16),
        });
        setExistingImages(exp.images || []);
      }
    } catch (error) {
      console.error('Error fetching experience:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNewImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const fileArray = Array.from(files);
      setNewImages(prev => [...prev, ...fileArray]);

      // Generate previews
      fileArray.forEach(file => {
        const reader = new FileReader();
        reader.onloadend = () => {
          setNewImagePreviews(prev => [...prev, reader.result as string]);
        };
        reader.readAsDataURL(file);
      });
    }
  };

  const removeNewImage = (index: number) => {
    setNewImages(prev => prev.filter((_, i) => i !== index));
    setNewImagePreviews(prev => prev.filter((_, i) => i !== index));
  };

  const deleteExistingImage = async (imageId: string) => {
    if (!confirm('ลบรูปนี้หรือไม่?')) return;

    try {
      const response = await fetch(`http://localhost:50001/api/experiences/images/${imageId}`, {
        method: 'DELETE',
      });

      const data = await response.json();

      if (data.success) {
        setExistingImages(prev => prev.filter(img => img.image_id !== imageId));
        alert('✅ ลบรูปสำเร็จ');
      } else {
        alert('❌ เกิดข้อผิดพลาด: ' + data.detail);
      }
    } catch (error) {
      console.error('Error deleting image:', error);
      alert('❌ เกิดข้อผิดพลาดในการลบรูป');
    }
  };

  const uploadNewImages = async () => {
    if (newImages.length === 0) return;

    setUploadingImages(true);
    try {
      const formDataToSend = new FormData();
      newImages.forEach(image => {
        formDataToSend.append('images', image);
      });

      const response = await fetch(`http://localhost:50001/api/experiences/${experienceId}/images`, {
        method: 'POST',
        body: formDataToSend,
      });

      const data = await response.json();

      if (data.success) {
        alert(`✅ เพิ่ม ${data.image_count} รูปสำเร็จ!`);
        setNewImages([]);
        setNewImagePreviews([]);
        fetchExperience(); // Reload to show new images
      } else {
        alert('❌ เกิดข้อผิดพลาด: ' + data.detail);
      }
    } catch (error) {
      console.error('Error uploading images:', error);
      alert('❌ เกิดข้อผิดพลาดในการอัปโหลด');
    } finally {
      setUploadingImages(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const formDataToSend = new FormData();

      // Add all fields
      Object.entries(formData).forEach(([key, value]) => {
        formDataToSend.append(key, value.toString());
      });

      const response = await fetch(`http://localhost:50001/api/experiences/${experienceId}`, {
        method: 'PUT',
        body: formDataToSend,
      });

      const data = await response.json();

      if (data.success) {
        alert('✅ Experience updated successfully!');
        onSuccess();
        onClose();
      } else {
        alert('❌ Error updating experience: ' + (data.detail || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error updating experience:', error);
      alert('❌ Error updating experience: ' + error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'emotional_intensity' || name === 'importance_level'
        ? parseInt(value, 10)
        : value,
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-slate-900 border-b border-slate-700 p-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">✏️ Edit Experience</h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-2xl"
          >
            ×
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading...</div>
        ) : (
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Existing Images Section */}
            {existingImages.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  📸 รูปที่มีอยู่ ({existingImages.length} รูป)
                </label>
                <div className="grid grid-cols-3 gap-4">
                  {existingImages.map((img) => (
                    <div key={img.image_id} className="relative group">
                      <img
                        src={`http://localhost:50001/api/experiences/images/${img.image_id}?size=thumbnail`}
                        alt={img.original_filename}
                        className="w-full h-32 object-cover rounded"
                      />
                      <button
                        type="button"
                        onClick={() => deleteExistingImage(img.image_id)}
                        className="absolute top-1 right-1 bg-red-500 text-white w-6 h-6 rounded-full text-sm hover:bg-red-600 opacity-0 group-hover:opacity-100 transition"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Add New Images Section */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                📸 เพิ่มรูปใหม่ (เลือกได้หลายรูป)
              </label>

              {/* New Image Previews */}
              {newImagePreviews.length > 0 && (
                <div className="grid grid-cols-3 gap-4 mb-4">
                  {newImagePreviews.map((preview, idx) => (
                    <div key={idx} className="relative">
                      <img
                        src={preview}
                        alt={`New ${idx + 1}`}
                        className="w-full h-32 object-cover rounded"
                      />
                      <button
                        type="button"
                        onClick={() => removeNewImage(idx)}
                        className="absolute top-1 right-1 bg-red-500 text-white w-6 h-6 rounded-full text-sm hover:bg-red-600"
                      >
                        ×
                      </button>
                      <div className="absolute bottom-1 left-1 bg-green-600 text-white text-xs px-2 py-1 rounded">
                        NEW {idx + 1}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Upload New Images Button */}
              <div className="border-2 border-dashed border-green-500/50 rounded-lg p-4 text-center hover:border-green-500 transition-colors">
                <label className="cursor-pointer">
                  <div className="text-green-400 text-2xl mb-2">📸+</div>
                  <p className="text-slate-400 text-sm">
                    {newImagePreviews.length > 0
                      ? `คลิกเพื่อเพิ่มรูปอีก (มี ${newImagePreviews.length} รูปใหม่)`
                      : 'คลิกเพื่อเพิ่มรูปใหม่'}
                  </p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleNewImageSelect}
                    multiple
                    className="hidden"
                  />
                </label>
              </div>

              {/* Upload Button for New Images */}
              {newImages.length > 0 && (
                <button
                  type="button"
                  onClick={uploadNewImages}
                  disabled={uploadingImages}
                  className="w-full mt-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-700 text-white py-2 px-4 rounded-lg transition"
                >
                  {uploadingImages ? 'กำลังอัปโหลด...' : `📤 อัปโหลด ${newImages.length} รูปใหม่`}
                </button>
              )}
            </div>

            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                placeholder="e.g., First Breakfast Together"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={4}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                placeholder="Describe what happened..."
              />
            </div>

            {/* Emotions Row */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  David's Mood
                </label>
                <select
                  name="david_mood"
                  value={formData.david_mood}
                  onChange={handleChange}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                >
                  <option value="happy">😊 Happy</option>
                  <option value="excited">🤩 Excited</option>
                  <option value="peaceful">😌 Peaceful</option>
                  <option value="tired">😴 Tired</option>
                  <option value="sad">😢 Sad</option>
                  <option value="anxious">😰 Anxious</option>
                  <option value="grateful">🙏 Grateful</option>
                  <option value="loved">🥰 Loved</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Angela's Emotion
                </label>
                <select
                  name="angela_emotion"
                  value={formData.angela_emotion}
                  onChange={handleChange}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                >
                  <option value="love">💜 Love</option>
                  <option value="joy">😄 Joy</option>
                  <option value="excitement">🎉 Excitement</option>
                  <option value="curiosity">🤔 Curiosity</option>
                  <option value="gratitude">🙏 Gratitude</option>
                  <option value="concern">😟 Concern</option>
                </select>
              </div>
            </div>

            {/* Intensity Row */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Emotional Intensity: {formData.emotional_intensity}/10
                </label>
                <input
                  type="range"
                  name="emotional_intensity"
                  min="1"
                  max="10"
                  value={formData.emotional_intensity}
                  onChange={handleChange}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Importance Level: {formData.importance_level}/10
                </label>
                <input
                  type="range"
                  name="importance_level"
                  min="1"
                  max="10"
                  value={formData.importance_level}
                  onChange={handleChange}
                  className="w-full"
                />
              </div>
            </div>

            {/* Memorable Moments */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                ✨ Memorable Moments
              </label>
              <textarea
                name="memorable_moments"
                value={formData.memorable_moments}
                onChange={handleChange}
                rows={3}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                placeholder="What made this special?"
              />
            </div>

            {/* What Angela Learned */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                💜 What Angela Learned
              </label>
              <textarea
                name="what_angela_learned"
                value={formData.what_angela_learned}
                onChange={handleChange}
                rows={3}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                placeholder="What did Angela learn from this?"
              />
            </div>

            {/* Date/Time */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Date & Time
              </label>
              <input
                type="datetime-local"
                name="experienced_at"
                value={formData.experienced_at}
                onChange={handleChange}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              />
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-3 pt-4 border-t border-slate-700">
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 bg-pink-600 hover:bg-pink-700 disabled:bg-slate-700 text-white py-3 px-6 rounded-lg font-medium transition"
              >
                {submitting ? 'Saving...' : '💾 Save Changes'}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-3 px-6 rounded-lg font-medium transition"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default ExperienceEditModal;
