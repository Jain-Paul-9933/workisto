// Shared shapes that mirror the Django/DRF API. Money and other DecimalFields
// arrive as strings (DRF renders Decimal as a string to avoid float rounding),
// so they're typed as `string` here, not `number`.

export type ServiceMode = "CHAT" | "ONSITE";
export type BookingType = "INSTANT" | "CONSULTATION_REQUIRED";
export type BookingStatus =
  | "PENDING_ESTIMATE"
  | "ESTIMATED"
  | "CONFIRMED"
  | "CANCELLED"
  | "COMPLETED";

export type LatLng = { latitude: number; longitude: number };

export type Provider = {
  id: number;
  full_name: string;
  bio: string;
  service_radius_km: string;
  accepting_bookings: boolean;
  rating_avg: string;
  rating_count: number;
  location: LatLng | null;
  created_at: string;
};

export type Category = {
  id: number;
  name: string;
  slug: string;
  description: string;
  default_duration_minutes: number;
};

export type Offering = {
  id: number;
  category: number;
  category_name: string;
  base_price: string;
  current_price: string;
  booking_type: BookingType;
  consultation_fee: string;
  supported_modes: ServiceMode[];
  duration_minutes: number;
  is_active: boolean;
};

export type Booking = {
  id: number;
  customer: number;
  provider: number;
  provider_name: string;
  offering: number;
  category_name: string;
  mode: ServiceMode;
  status: BookingStatus;
  start_at: string | null;
  end_at: string | null;
  price: string | null;
  consultation_fee: string;
  estimate_amount: string | null;
  notes: string;
  created_at: string;
};

// --- Customer-facing / public read shapes ----------------------------------

// A single geo-search hit. Normalised in the search route so it's the same
// whether it came from the FastAPI service (numbers) or the Django fallback
// (Decimal-as-string) — rating_avg is always a number here.
export type SearchResult = {
  id: number;
  full_name: string;
  bio: string;
  rating_avg: number;
  rating_count: number;
  distance_km: number;
};

export type PublicOffering = {
  id: number;
  category: number;
  category_name: string;
  current_price: string;
  booking_type: BookingType;
  consultation_fee: string;
  supported_modes: ServiceMode[];
  duration_minutes: number;
};

export type PublicProvider = {
  id: number;
  full_name: string;
  bio: string;
  rating_avg: string;
  rating_count: number;
  location: LatLng | null;
  offerings: PublicOffering[];
};

export type Review = {
  id: number;
  rating: number;
  comment: string;
  reviewer: string;
  created_at: string;
};

export type PaymentKind = "CONSULTATION" | "ADVANCE" | "FINAL";
export type PaymentStatus = "PENDING" | "SUCCEEDED" | "FAILED" | "REFUNDED";

export type Payment = {
  id: number;
  booking: number;
  kind: PaymentKind;
  amount: string;
  currency: string;
  status: PaymentStatus;
  client_secret: string;
  created_at: string;
};

export type ChatMessage = {
  id: number;
  booking: number;
  sender: number;
  sender_email: string;
  body: string;
  created_at: string;
};
