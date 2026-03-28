-- ============================================================================
-- ServiceHub PostgreSQL Schema for Supabase
-- ============================================================================
-- This file contains the complete database schema for ServiceHub
-- Compatible with Supabase PostgreSQL
-- All tables are linked to Supabase auth.users table
-- ============================================================================

-- ============================================================================
-- ENUMS (Custom Types)
-- ============================================================================

-- Booking status enum
CREATE TYPE booking_status AS ENUM (
    'pending',
    'confirmed',
    'in_progress',
    'completed',
    'cancelled',
    'declined'
);

-- User role enum
CREATE TYPE user_role AS ENUM (
    'customer',
    'provider',
    'admin'
);

-- Service status enum
CREATE TYPE service_status AS ENUM (
    'active',
    'inactive',
    'archived'
);

-- Message status enum
CREATE TYPE message_status AS ENUM (
    'sent',
    'delivered',
    'read'
);

-- Subscription status enum
CREATE TYPE subscription_status AS ENUM (
    'active',
    'cancelled',
    'expired',
    'pending'
);

-- ============================================================================
-- USERS TABLE (Extended Supabase auth.users)
-- ============================================================================
-- Links to Supabase auth.users table
-- Extends auth profile with ServiceHub-specific fields

CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    -- User Information
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    bio TEXT,
    profile_picture_url TEXT,
    phone_number TEXT,

    -- Role and Status
    role user_role DEFAULT 'customer' NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_verified BOOLEAN DEFAULT false NOT NULL,
    is_email_verified BOOLEAN DEFAULT false NOT NULL,

    -- Profile Completion
    profile_completed BOOLEAN DEFAULT false,

    -- Ratings and Stats
    average_rating DECIMAL(3,2) DEFAULT 0,
    total_reviews INTEGER DEFAULT 0,
    total_bookings INTEGER DEFAULT 0,
    completion_rate DECIMAL(5,2) DEFAULT 0,

    -- Location
    city TEXT,
    state TEXT,
    country TEXT,
    postal_code TEXT,

    -- Preferences
    preferred_language TEXT DEFAULT 'en',
    timezone TEXT DEFAULT 'UTC',
    notifications_enabled BOOLEAN DEFAULT true,

    -- Account Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_login_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes on users table
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_username ON public.users(username);
CREATE INDEX idx_users_role ON public.users(role);
CREATE INDEX idx_users_is_active ON public.users(is_active);
CREATE INDEX idx_users_created_at ON public.users(created_at DESC);
CREATE INDEX idx_users_city_country ON public.users(city, country);

-- ============================================================================
-- PROVIDER PROFILES TABLE
-- ============================================================================
-- Stores additional information for providers

CREATE TABLE public.provider_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,

    -- Professional Information
    company_name TEXT,
    business_license TEXT,
    tax_id TEXT,
    business_category TEXT,
    years_of_experience INTEGER,
    certifications TEXT[], -- Array of certifications

    -- Availability
    is_available BOOLEAN DEFAULT true,
    availability_schedule JSONB, -- Stores availability schedule

    -- Service Area
    service_radius_km INTEGER DEFAULT 50,

    -- Bank Account (for payments)
    bank_account_holder TEXT,
    bank_account_number TEXT (encrypted), -- In production, use Supabase encryption
    bank_routing_number TEXT (encrypted),

    -- Statistics
    total_services INTEGER DEFAULT 0,
    completed_services INTEGER DEFAULT 0,
    response_time_minutes INTEGER,
    cancellation_rate DECIMAL(5,2) DEFAULT 0,

    -- Verification
    is_verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP WITH TIME ZONE,
    verification_documents JSONB, -- Array of document URLs

    -- Account Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes on provider_profiles table
CREATE INDEX idx_provider_profiles_provider_id ON public.provider_profiles(provider_id);
CREATE INDEX idx_provider_profiles_is_available ON public.provider_profiles(is_available);
CREATE INDEX idx_provider_profiles_is_verified ON public.provider_profiles(is_verified);
CREATE INDEX idx_provider_profiles_created_at ON public.provider_profiles(created_at DESC);

-- ============================================================================
-- SERVICES TABLE
-- ============================================================================
-- Stores service listings

CREATE TABLE public.services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    -- Service Information
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    tags TEXT[], -- Array of tags for searching

    -- Pricing
    price_per_hour DECIMAL(10,2) NOT NULL,
    minimum_hours INTEGER DEFAULT 1,
    currency TEXT DEFAULT 'USD',

    -- Service Details
    service_duration_hours INTEGER,
    includes_materials BOOLEAN DEFAULT false,
    materials_cost DECIMAL(10,2),

    -- Status and Visibility
    status service_status DEFAULT 'active' NOT NULL,
    is_featured BOOLEAN DEFAULT false,

    -- Media
    thumbnail_url TEXT,
    image_urls TEXT[], -- Array of service images
    video_url TEXT,

    -- Ratings
    average_rating DECIMAL(3,2) DEFAULT 0,
    total_reviews INTEGER DEFAULT 0,
    total_bookings INTEGER DEFAULT 0,

    -- Availability
    is_available BOOLEAN DEFAULT true,
    availability_start_date DATE,
    availability_end_date DATE,
    max_monthly_bookings INTEGER,

    -- Account Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes on services table
CREATE INDEX idx_services_provider_id ON public.services(provider_id);
CREATE INDEX idx_services_category ON public.services(category);
CREATE INDEX idx_services_subcategory ON public.services(subcategory);
CREATE INDEX idx_services_status ON public.services(status);
CREATE INDEX idx_services_is_available ON public.services(is_available);
CREATE INDEX idx_services_is_featured ON public.services(is_featured);
CREATE INDEX idx_services_title_tsvector ON public.services USING GIN(to_tsvector('english', title));
CREATE INDEX idx_services_tags ON public.services USING GIN(tags);
CREATE INDEX idx_services_created_at ON public.services(created_at DESC);

-- ============================================================================
-- PROVIDER SERVICES MAPPING TABLE
-- ============================================================================
-- Links providers to multiple services they offer

CREATE TABLE public.provider_services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES public.services(id) ON DELETE CASCADE,

    -- Service Customization per Provider
    custom_price_per_hour DECIMAL(10,2),
    custom_description TEXT,
    is_primary BOOLEAN DEFAULT false,

    -- Performance Metrics
    completion_count INTEGER DEFAULT 0,
    cancellation_count INTEGER DEFAULT 0,
    average_customer_rating DECIMAL(3,2) DEFAULT 0,

    -- Account Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    UNIQUE(provider_id, service_id)
);

-- Indexes on provider_services table
CREATE INDEX idx_provider_services_provider_id ON public.provider_services(provider_id);
CREATE INDEX idx_provider_services_service_id ON public.provider_services(service_id);
CREATE INDEX idx_provider_services_is_primary ON public.provider_services(is_primary);

-- ============================================================================
-- BOOKINGS TABLE
-- ============================================================================
-- Stores service bookings

CREATE TABLE public.bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    service_id UUID NOT NULL REFERENCES public.services(id) ON DELETE RESTRICT,
    provider_id UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    customer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    -- Booking Status
    status booking_status DEFAULT 'pending' NOT NULL,

    -- Booking Details
    scheduled_date DATE NOT NULL,
    scheduled_time TIME NOT NULL,
    duration_hours INTEGER NOT NULL,

    -- Pricing
    hourly_rate DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    deposit_amount DECIMAL(10,2),
    currency TEXT DEFAULT 'USD',

    -- Additional Information
    customer_notes TEXT,
    provider_notes TEXT,
    location TEXT,
    address TEXT,
    city TEXT,
    postal_code TEXT,

    -- Cancellation
    cancelled_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    cancellation_reason TEXT,
    cancelled_at TIMESTAMP WITH TIME ZONE,

    -- Completion
    completed_at TIMESTAMP WITH TIME ZONE,
    actual_duration_hours DECIMAL(5,2),

    -- Review and Rating
    customer_review_id UUID,
    provider_review_id UUID,

    -- Account Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes on bookings table
CREATE INDEX idx_bookings_service_id ON public.bookings(service_id);
CREATE INDEX idx_bookings_provider_id ON public.bookings(provider_id);
CREATE INDEX idx_bookings_customer_id ON public.bookings(customer_id);
CREATE INDEX idx_bookings_status ON public.bookings(status);
CREATE INDEX idx_bookings_scheduled_date ON public.bookings(scheduled_date);
CREATE INDEX idx_bookings_created_at ON public.bookings(created_at DESC);
CREATE INDEX idx_bookings_provider_customer ON public.bookings(provider_id, customer_id);

-- ============================================================================
-- MESSAGES TABLE
-- ============================================================================
-- Stores messages between users

CREATE TABLE public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    sender_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    booking_id UUID REFERENCES public.bookings(id) ON DELETE SET NULL,

    -- Message Content
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'text', -- text, image, file, etc.

    -- Media Attachment
    attachment_url TEXT,
    attachment_type TEXT,

    -- Message Status
    status message_status DEFAULT 'sent' NOT NULL,
    read_at TIMESTAMP WITH TIME ZONE,

    -- Account Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes on messages table
CREATE INDEX idx_messages_sender_id ON public.messages(sender_id);
CREATE INDEX idx_messages_recipient_id ON public.messages(recipient_id);
CREATE INDEX idx_messages_booking_id ON public.messages(booking_id);
CREATE INDEX idx_messages_status ON public.messages(status);
CREATE INDEX idx_messages_created_at ON public.messages(created_at DESC);
CREATE INDEX idx_messages_sender_recipient ON public.messages(sender_id, recipient_id);

-- ============================================================================
-- REVIEWS TABLE
-- ============================================================================
-- Stores reviews and ratings

CREATE TABLE public.reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    booking_id UUID NOT NULL UNIQUE REFERENCES public.bookings(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    reviewee_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES public.services(id) ON DELETE CASCADE,

    -- Review Content
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title TEXT NOT NULL,
    comment TEXT,

    -- Review Aspects
    quality_rating INTEGER CHECK (quality_rating >= 1 AND quality_rating <= 5),
    professionalism_rating INTEGER CHECK (professionalism_rating >= 1 AND professionalism_rating <= 5),
    communication_rating INTEGER CHECK (communication_rating >= 1 AND communication_rating <= 5),
    punctuality_rating INTEGER CHECK (punctuality_rating >= 1 AND punctuality_rating <= 5),

    -- Media
    image_urls TEXT[], -- Array of review images

    -- Response
    provider_response TEXT,
    provider_response_at TIMESTAMP WITH TIME ZONE,

    -- Verification
    is_verified_purchase BOOLEAN DEFAULT true,

    -- Account Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes on reviews table
CREATE INDEX idx_reviews_booking_id ON public.reviews(booking_id);
CREATE INDEX idx_reviews_reviewer_id ON public.reviews(reviewer_id);
CREATE INDEX idx_reviews_reviewee_id ON public.reviews(reviewee_id);
CREATE INDEX idx_reviews_service_id ON public.reviews(service_id);
CREATE INDEX idx_reviews_rating ON public.reviews(rating);
CREATE INDEX idx_reviews_created_at ON public.reviews(created_at DESC);

-- ============================================================================
-- SUBSCRIPTIONS TABLE
-- ============================================================================
-- Stores subscription plans for providers

CREATE TABLE public.subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relationships
    provider_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,

    -- Subscription Type
    plan_name TEXT NOT NULL,
    plan_tier TEXT NOT NULL, -- basic, professional, premium

    -- Pricing
    price_per_month DECIMAL(10,2) NOT NULL,
    currency TEXT DEFAULT 'USD',

    -- Status
    status subscription_status DEFAULT 'pending' NOT NULL,

    -- Dates
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    renewal_date TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    cancellation_reason TEXT,

    -- Payment Information
    payment_method TEXT,
    auto_renew BOOLEAN DEFAULT true,

    -- Features
    max_active_services INTEGER,
    featured_listings_count INTEGER DEFAULT 0,
    priority_support BOOLEAN DEFAULT false,
    analytics_dashboard BOOLEAN DEFAULT false,

    -- Account Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes on subscriptions table
CREATE INDEX idx_subscriptions_provider_id ON public.subscriptions(provider_id);
CREATE INDEX idx_subscriptions_status ON public.subscriptions(status);
CREATE INDEX idx_subscriptions_plan_tier ON public.subscriptions(plan_tier);
CREATE INDEX idx_subscriptions_start_date ON public.subscriptions(start_date);
CREATE INDEX idx_subscriptions_renewal_date ON public.subscriptions(renewal_date);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT TIMESTAMPS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON public.users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for provider_profiles table
CREATE TRIGGER update_provider_profiles_updated_at
BEFORE UPDATE ON public.provider_profiles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for services table
CREATE TRIGGER update_services_updated_at
BEFORE UPDATE ON public.services
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for provider_services table
CREATE TRIGGER update_provider_services_updated_at
BEFORE UPDATE ON public.provider_services
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for bookings table
CREATE TRIGGER update_bookings_updated_at
BEFORE UPDATE ON public.bookings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for messages table
CREATE TRIGGER update_messages_updated_at
BEFORE UPDATE ON public.messages
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for reviews table
CREATE TRIGGER update_reviews_updated_at
BEFORE UPDATE ON public.reviews
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for subscriptions table
CREATE TRIGGER update_subscriptions_updated_at
BEFORE UPDATE ON public.subscriptions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.provider_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.services ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.provider_services ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- Users can view all profiles
CREATE POLICY "Users can view all profiles" ON public.users
FOR SELECT USING (TRUE);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON public.users
FOR UPDATE USING (auth.uid() = id);

-- Anyone can view active services
CREATE POLICY "Anyone can view active services" ON public.services
FOR SELECT USING (status = 'active');

-- Providers can view their own services
CREATE POLICY "Providers can view own services" ON public.services
FOR SELECT USING (provider_id = auth.uid());

-- Providers can update their own services
CREATE POLICY "Providers can update own services" ON public.services
FOR UPDATE USING (provider_id = auth.uid());

-- Users can view their own bookings
CREATE POLICY "Users can view own bookings" ON public.bookings
FOR SELECT USING (
    customer_id = auth.uid() OR
    provider_id = auth.uid()
);

-- Customers can create bookings
CREATE POLICY "Customers can create bookings" ON public.bookings
FOR INSERT WITH CHECK (customer_id = auth.uid());

-- Users can view their own messages
CREATE POLICY "Users can view own messages" ON public.messages
FOR SELECT USING (
    sender_id = auth.uid() OR
    recipient_id = auth.uid()
);

-- Users can create messages
CREATE POLICY "Users can create messages" ON public.messages
FOR INSERT WITH CHECK (sender_id = auth.uid());

-- Users can view reviews for completed bookings
CREATE POLICY "Users can view reviews" ON public.reviews
FOR SELECT USING (TRUE);

-- Users can create reviews for their bookings
CREATE POLICY "Users can create reviews" ON public.reviews
FOR INSERT WITH CHECK (reviewer_id = auth.uid());

-- Providers can view their subscriptions
CREATE POLICY "Providers can view own subscriptions" ON public.subscriptions
FOR SELECT USING (provider_id = auth.uid());

-- ============================================================================
-- PERFORMANCE OPTIMIZATION QUERIES
-- ============================================================================

-- Full-text search index on services
CREATE INDEX idx_services_search ON public.services USING GIN (
    to_tsvector('english', title || ' ' || description)
);

-- Composite index for common booking queries
CREATE INDEX idx_bookings_status_date ON public.bookings(status, scheduled_date DESC);

-- Composite index for provider analytics
CREATE INDEX idx_provider_analytics ON public.bookings(
    provider_id,
    status,
    created_at DESC
);

-- Composite index for customer history
CREATE INDEX idx_customer_history ON public.bookings(
    customer_id,
    status,
    created_at DESC
);

-- ============================================================================
-- GRANTS AND PERMISSIONS
-- ============================================================================

-- Grant anon user read access to services
GRANT SELECT ON public.services TO anon;

-- Grant authenticated users access to their own data
GRANT SELECT, UPDATE ON public.users TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.bookings TO authenticated;
GRANT SELECT, INSERT ON public.messages TO authenticated;
GRANT SELECT, INSERT ON public.reviews TO authenticated;

-- Grant providers access to their profiles and services
GRANT SELECT, INSERT, UPDATE ON public.provider_profiles TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.services TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.subscriptions TO authenticated;

-- ============================================================================
-- SCHEMA DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE public.users IS 'User accounts linked to Supabase auth.users';
COMMENT ON TABLE public.provider_profiles IS 'Extended profile information for service providers';
COMMENT ON TABLE public.services IS 'Service listings offered by providers';
COMMENT ON TABLE public.provider_services IS 'Mapping of providers to services they offer';
COMMENT ON TABLE public.bookings IS 'Service bookings/orders placed by customers';
COMMENT ON TABLE public.messages IS 'Messages between users';
COMMENT ON TABLE public.reviews IS 'Reviews and ratings for completed services';
COMMENT ON TABLE public.subscriptions IS 'Subscription plans for premium features';

COMMENT ON COLUMN public.users.role IS 'User role: customer, provider, or admin';
COMMENT ON COLUMN public.bookings.status IS 'Booking status: pending, confirmed, in_progress, completed, cancelled, declined';
COMMENT ON COLUMN public.services.status IS 'Service status: active, inactive, or archived';
COMMENT ON COLUMN public.messages.status IS 'Message status: sent, delivered, or read';

-- ============================================================================
-- PERFORMANCE STATISTICS
-- ============================================================================

-- Analyze tables for query optimization
ANALYZE public.users;
ANALYZE public.provider_profiles;
ANALYZE public.services;
ANALYZE public.provider_services;
ANALYZE public.bookings;
ANALYZE public.messages;
ANALYZE public.reviews;
ANALYZE public.subscriptions;

-- ============================================================================
-- SCHEMA CREATION COMPLETE
-- ============================================================================
-- All tables, relationships, indexes, and security policies have been created.
-- The schema is ready for use with Supabase.
-- ============================================================================

