import { useState, type FormEvent } from 'react';

interface FormState {
  name: string;
  email: string;
  company: string;
  message: string;
}

interface FieldErrors {
  name?: string;
  email?: string;
  message?: string;
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function ContactForm() {
  const [form, setForm] = useState<FormState>({
    name: '',
    email: '',
    company: '',
    message: '',
  });
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<'idle' | 'pending' | 'success' | 'error'>('idle');

  const validate = (): FieldErrors => {
    const errs: FieldErrors = {};
    if (!form.name.trim()) errs.name = 'Name is required.';
    if (!form.email.trim()) {
      errs.email = 'Email is required.';
    } else if (!EMAIL_REGEX.test(form.email)) {
      errs.email = 'Please enter a valid email address.';
    }
    if (!form.message.trim()) errs.message = 'Message is required.';
    return errs;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    // Clear field error on change
    if (errors[name as keyof FieldErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    setStatus('pending');

    const action = (import.meta as any).env?.PUBLIC_FORM_ACTION as string | undefined;

    if (!action) {
      // No endpoint configured — show error
      setStatus('error');
      return;
    }

    try {
      const res = await fetch(action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });

      if (res.ok) {
        setStatus('success');
        setForm({ name: '', email: '', company: '', message: '' });
      } else {
        setStatus('error');
      }
    } catch {
      setStatus('error');
    }
  };

  if (status === 'success') {
    return (
      <div className="bg-green-50 border border-green-200 rounded-xl p-8 text-center">
        <div className="text-4xl mb-3">✅</div>
        <h3 className="text-xl font-semibold text-green-800 mb-2">Message sent!</h3>
        <p className="text-green-700">
          Thanks for reaching out. We'll be in touch within one business day.
        </p>
        <button
          type="button"
          onClick={() => setStatus('idle')}
          className="mt-4 text-sm text-green-600 underline hover:text-green-800"
        >
          Send another message
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-5">

      {status === 'error' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
          Something went wrong. Please try again or email us directly.
        </div>
      )}

      {/* Name */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-1">
          Name <span className="text-red-500">*</span>
        </label>
        <input
          id="name"
          name="name"
          type="text"
          autoComplete="name"
          value={form.name}
          onChange={handleChange}
          placeholder="Jane Smith"
          className={`w-full px-4 py-2.5 border rounded-md text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 transition ${
            errors.name ? 'border-red-400 bg-red-50' : 'border-slate-300 bg-white'
          }`}
        />
        {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name}</p>}
      </div>

      {/* Email */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">
          Email <span className="text-red-500">*</span>
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={handleChange}
          placeholder="jane@company.com"
          className={`w-full px-4 py-2.5 border rounded-md text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 transition ${
            errors.email ? 'border-red-400 bg-red-50' : 'border-slate-300 bg-white'
          }`}
        />
        {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email}</p>}
      </div>

      {/* Company (optional) */}
      <div>
        <label htmlFor="company" className="block text-sm font-medium text-slate-700 mb-1">
          Company <span className="text-slate-400 font-normal">(optional)</span>
        </label>
        <input
          id="company"
          name="company"
          type="text"
          autoComplete="organization"
          value={form.company}
          onChange={handleChange}
          placeholder="Acme Ltd"
          className="w-full px-4 py-2.5 border border-slate-300 rounded-md text-slate-900 placeholder-slate-400 bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 transition"
        />
      </div>

      {/* Message */}
      <div>
        <label htmlFor="message" className="block text-sm font-medium text-slate-700 mb-1">
          Message <span className="text-red-500">*</span>
        </label>
        <textarea
          id="message"
          name="message"
          rows={5}
          value={form.message}
          onChange={handleChange}
          placeholder="Tell us about your business and what you're looking to achieve with LinkedIn..."
          className={`w-full px-4 py-2.5 border rounded-md text-slate-900 placeholder-slate-400 resize-y focus:outline-none focus:ring-2 focus:ring-primary-500 transition ${
            errors.message ? 'border-red-400 bg-red-50' : 'border-slate-300 bg-white'
          }`}
        />
        {errors.message && <p className="mt-1 text-xs text-red-600">{errors.message}</p>}
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={status === 'pending'}
        className="w-full flex justify-center items-center gap-2 px-6 py-3 bg-primary-800 text-white font-semibold rounded-md hover:bg-primary-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
      >
        {status === 'pending' ? (
          <>
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Sending…
          </>
        ) : (
          'Send Message'
        )}
      </button>

      <p className="text-xs text-slate-400 text-center">
        We typically respond within one business day.
      </p>
    </form>
  );
}
