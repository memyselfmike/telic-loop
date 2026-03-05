import { useState, type FormEvent } from 'react';
import '../styles/contact-form.css';

interface FormData {
  name: string;
  email: string;
  company: string;
  message: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  message?: string;
}

export default function ContactForm() {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    company: '',
    message: ''
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Name validation
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!emailRegex.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Message validation
    if (!formData.message.trim()) {
      newErrors.message = 'Message is required';
    } else if (formData.message.trim().length < 10) {
      newErrors.message = 'Message must be at least 10 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitStatus('idle');

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Submit to Payload CMS FormSubmissions collection
      const response = await fetch('http://localhost:3000/api/form-submissions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Form submission failed');
      }

      setSubmitStatus('success');
      setFormData({ name: '', email: '', company: '', message: '' });
      setErrors({});

      // Reset success message after 5 seconds
      setTimeout(() => setSubmitStatus('idle'), 5000);
    } catch (error) {
      console.error('Form submission error:', error);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof FormData) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }));
    // Clear error for this field when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <form className="contact-form" onSubmit={handleSubmit} noValidate>
      {/* Name Field */}
      <div className="form-group">
        <label htmlFor="name" className="form-label">
          Name <span className="required">*</span>
        </label>
        <input
          type="text"
          id="name"
          className={`form-input ${errors.name ? 'has-error' : ''}`}
          value={formData.name}
          onChange={handleChange('name')}
          placeholder="Your full name"
          disabled={isSubmitting}
        />
        {errors.name && <span className="error-message">{errors.name}</span>}
      </div>

      {/* Email Field */}
      <div className="form-group">
        <label htmlFor="email" className="form-label">
          Email <span className="required">*</span>
        </label>
        <input
          type="email"
          id="email"
          className={`form-input ${errors.email ? 'has-error' : ''}`}
          value={formData.email}
          onChange={handleChange('email')}
          placeholder="your.email@company.com"
          disabled={isSubmitting}
        />
        {errors.email && <span className="error-message">{errors.email}</span>}
      </div>

      {/* Company Field */}
      <div className="form-group">
        <label htmlFor="company" className="form-label">
          Company
        </label>
        <input
          type="text"
          id="company"
          className="form-input"
          value={formData.company}
          onChange={handleChange('company')}
          placeholder="Your company name (optional)"
          disabled={isSubmitting}
        />
      </div>

      {/* Message Field */}
      <div className="form-group">
        <label htmlFor="message" className="form-label">
          Message <span className="required">*</span>
        </label>
        <textarea
          id="message"
          className={`form-input form-textarea ${errors.message ? 'has-error' : ''}`}
          value={formData.message}
          onChange={handleChange('message')}
          placeholder="Tell us about your LinkedIn lead generation goals..."
          rows={6}
          disabled={isSubmitting}
        />
        {errors.message && <span className="error-message">{errors.message}</span>}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        className="submit-button"
        disabled={isSubmitting}
      >
        {isSubmitting ? (
          <>
            <span className="spinner"></span>
            Sending...
          </>
        ) : (
          'Book Discovery Call'
        )}
      </button>

      {/* Success Message */}
      {submitStatus === 'success' && (
        <div className="status-message success-message">
          <span className="status-icon">✓</span>
          <div>
            <strong>Message sent successfully!</strong>
            <p>We'll get back to you within 24 hours.</p>
          </div>
        </div>
      )}

      {/* Error Message */}
      {submitStatus === 'error' && (
        <div className="status-message error-message-box">
          <span className="status-icon">⚠</span>
          <div>
            <strong>Something went wrong</strong>
            <p>Please try again or email us at hello@beep2b.com</p>
          </div>
        </div>
      )}
    </form>
  );
}
