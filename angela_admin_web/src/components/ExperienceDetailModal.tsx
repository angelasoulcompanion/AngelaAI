/**
 * Experience Detail Modal Component
 * Shows full experience details with all images
 */

import React, { useEffect, useState } from 'react';

interface Image {
  image_id: string;
  original_filename: string;
  image_caption?: string;
  gps_latitude?: number;
  gps_longitude?: number;
  taken_at: string;
}

interface Experience {
  experience_id: string;
  title: string;
  description?: string;
  experienced_at: string;
  david_mood: string;
  angela_emotion: string;
  emotional_intensity: number;
  importance_level: number;
  memorable_moments?: string;
  what_angela_learned?: string;
  place_name: string;
  place_type?: string;
  area?: string;
  images: Image[];
}

interface ExperienceDetailModalProps {
  experienceId: string;
  isOpen: boolean;
  onClose: () => void;
  onEdit?: (experienceId: string) => void;
  onDelete?: (experienceId: string) => void;
}

const ExperienceDetailModal: React.FC<ExperienceDetailModalProps> = ({
  experienceId,
  isOpen,
  onClose,
  onEdit,
  onDelete,
}) => {
  const [experience, setExperience] = useState<Experience | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);

  useEffect(() => {
    if (isOpen && experienceId) {
      fetchExperienceDetail();
    }
  }, [isOpen, experienceId]);

  const fetchExperienceDetail = async () => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:50001/api/experiences/${experienceId}`);
      const data = await response.json();

      if (data.success) {
        console.log('Experience data:', data.experience);
        console.log('Images:', data.experience.images);
        setExperience(data.experience);
      }
    } catch (error) {
      console.error('Error fetching experience:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMoodEmoji = (mood: string) => {
    const moodEmojis: Record<string, string> = {
      happy: '😊',
      excited: '🤩',
      peaceful: '😌',
      tired: '😴',
      sad: '😢',
      anxious: '😰',
      grateful: '🙏',
      loved: '🥰',
    };
    return moodEmojis[mood] || '😊';
  };

  const getEmotionColor = (emotion: string) => {
    const colors: Record<string, string> = {
      love: 'text-pink-400',
      joy: 'text-yellow-400',
      excitement: 'text-orange-400',
      curiosity: 'text-blue-400',
      gratitude: 'text-purple-400',
      concern: 'text-red-400',
    };
    return colors[emotion] || 'text-pink-400';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 rounded-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-slate-900 border-b border-slate-700 p-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">
            {loading ? 'Loading...' : experience?.title}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-2xl"
          >
            ×
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-slate-400">Loading experience...</div>
        ) : experience ? (
          <div className="p-6 space-y-6">
            {/* Images Gallery */}
            {experience.images && experience.images.length > 0 && (
              <div className="space-y-4">
                {/* Main Image */}
                <div className="relative bg-slate-800 rounded-lg overflow-hidden">
                  <img
                    src={`http://localhost:50001/api/experiences/images/${experience.images[selectedImageIndex].image_id}?size=original`}
                    alt={experience.images[selectedImageIndex].image_caption || 'Experience photo'}
                    className="w-full h-auto max-h-96 object-contain"
                  />
                  {experience.images[selectedImageIndex].image_caption && (
                    <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-60 p-3">
                      <p className="text-white text-sm">
                        {experience.images[selectedImageIndex].image_caption}
                      </p>
                    </div>
                  )}
                </div>

                {/* Thumbnails */}
                {experience.images.length > 1 && (
                  <div className="flex gap-2 overflow-x-auto">
                    {experience.images.map((img, idx) => (
                      <button
                        key={img.image_id}
                        onClick={() => setSelectedImageIndex(idx)}
                        className={`flex-shrink-0 rounded overflow-hidden border-2 ${
                          idx === selectedImageIndex
                            ? 'border-pink-500'
                            : 'border-slate-700'
                        }`}
                      >
                        <img
                          src={`http://localhost:50001/api/experiences/images/${img.image_id}?size=thumbnail`}
                          alt={`Thumbnail ${idx + 1}`}
                          className="w-20 h-20 object-cover"
                        />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Place Info */}
            <div className="bg-slate-800 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-2">📍 Place</h3>
              <p className="text-white">{experience.place_name}</p>
              {experience.area && (
                <p className="text-slate-400 text-sm">{experience.area}</p>
              )}
            </div>

            {/* Emotions & Ratings */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-800 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-slate-400 mb-2">David's Mood</h3>
                <p className="text-lg">
                  <span className="mr-2">{getMoodEmoji(experience.david_mood)}</span>
                  <span className="text-white capitalize">{experience.david_mood}</span>
                </p>
              </div>

              <div className="bg-slate-800 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-slate-400 mb-2">Angela's Emotion</h3>
                <p className="text-lg">
                  <span className="mr-2">💜</span>
                  <span className={`capitalize ${getEmotionColor(experience.angela_emotion)}`}>
                    {experience.angela_emotion}
                  </span>
                </p>
              </div>

              <div className="bg-slate-800 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-slate-400 mb-2">Emotional Intensity</h3>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-pink-500 h-2 rounded-full"
                      style={{ width: `${(experience.emotional_intensity / 10) * 100}%` }}
                    />
                  </div>
                  <span className="text-white">{experience.emotional_intensity}/10</span>
                </div>
              </div>

              <div className="bg-slate-800 rounded-lg p-4">
                <h3 className="text-sm font-semibold text-slate-400 mb-2">Importance</h3>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-yellow-500 h-2 rounded-full"
                      style={{ width: `${(experience.importance_level / 10) * 100}%` }}
                    />
                  </div>
                  <span className="text-white">{experience.importance_level}/10</span>
                </div>
              </div>
            </div>

            {/* Description */}
            {experience.description && (
              <div className="bg-slate-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-2">Description</h3>
                <p className="text-slate-300 whitespace-pre-wrap">{experience.description}</p>
              </div>
            )}

            {/* Memorable Moments */}
            {experience.memorable_moments && (
              <div className="bg-slate-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-2">✨ Memorable Moments</h3>
                <p className="text-slate-300 whitespace-pre-wrap">{experience.memorable_moments}</p>
              </div>
            )}

            {/* What Angela Learned */}
            {experience.what_angela_learned && (
              <div className="bg-slate-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-2">💜 What Angela Learned</h3>
                <p className="text-slate-300 whitespace-pre-wrap">{experience.what_angela_learned}</p>
              </div>
            )}

            {/* Date */}
            <div className="text-center text-slate-400 text-sm">
              {new Date(experience.experienced_at).toLocaleString('en-US', {
                dateStyle: 'long',
                timeStyle: 'short',
              })}
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4 border-t border-slate-700">
              {onEdit && (
                <button
                  onClick={() => {
                    onEdit(experienceId);
                    onClose();
                  }}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition"
                >
                  ✏️ Edit
                </button>
              )}
              {onDelete && (
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to delete this experience?')) {
                      onDelete(experienceId);
                      onClose();
                    }
                  }}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg transition"
                >
                  🗑️ Delete
                </button>
              )}
              <button
                onClick={onClose}
                className="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2 px-4 rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        ) : (
          <div className="p-8 text-center text-slate-400">Experience not found</div>
        )}
      </div>
    </div>
  );
};

export default ExperienceDetailModal;
