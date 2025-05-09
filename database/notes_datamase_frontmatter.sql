-- Notes Application Database Schema
-- PostgreSQL 13+ compatible

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" ;
CREATE EXTENSION IF NOT EXISTS "pgcrypto" ;

-- Enable full text search and vector extensions
CREATE EXTENSION IF NOT EXISTS "pg_trgm" ;

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username VARCHAR(255) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_salt VARCHAR(255) NOT NULL
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  avatar_url TEXT,
  preferences JSONB DEFAULT '{}',
  is_active BOOLEAN DEFAULT TRUE,
  is_test_user BOOLEAN DEFAULT FALSE,
  last_login_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Folders table for hierarchical organization
CREATE TABLE IF NOT EXISTS folders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL,
  description TEXT,
  parent_id UUID REFERENCES folders(id) ON DELETE CASCADE,
  is_archived BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, parent_id, slug)
);

-- Notes table
CREATE TABLE IF NOT EXISTS notes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  folder_id UUID REFERENCES folders(id) ON DELETE SET NULL,
  title VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL,
  description TEXT,
  -- START OF METADATA HYBRID APPROACH MODIFICATIONS
  -- Keep existing flexible metadata field
  metadata JSONB DEFAULT '{}',
  -- Add common structured frontmatter fields for better query performance
  -- These fields mirror common frontmatter properties in note-taking apps
  fm_status VARCHAR(50),                      -- Common frontmatter field: status (draft, published, archived)
  fm_priority INTEGER,                        -- Common frontmatter field: priority (1-5)
  fm_due_date DATE,                           -- Common frontmatter field: due date
  fm_author VARCHAR(255),                     -- Common frontmatter field: author
  fm_category VARCHAR(100),                   -- Common frontmatter field: category
  fm_template VARCHAR(255),                   -- Common frontmatter field: template reference
  fm_type VARCHAR(100),                       -- Common frontmatter field: note type
  fm_last_reviewed_at TIMESTAMP WITH TIME ZONE, -- Common frontmatter field: last reviewed date
  -- END OF METADATA HYBRID APPROACH MODIFICATIONS
  is_pinned BOOLEAN DEFAULT FALSE,
  is_archived BOOLEAN DEFAULT FALSE,
  is_public BOOLEAN DEFAULT FALSE,
  view_count INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, slug)
);

-- Tags table
CREATE TABLE IF NOT EXISTS tags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  color VARCHAR(7) DEFAULT '#607D8B', -- Default color hex
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, name)
);

-- Note-tag relationship
CREATE TABLE IF NOT EXISTS note_tags (
  note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  PRIMARY KEY (note_id, tag_id)
);

-- Sub-notes table
CREATE TABLE IF NOT EXISTS sub_notes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL, -- 'text', 'image', 'code', 'markdown', 'audio', 'video', 'file', etc.
  position FLOAT NOT NULL, -- Using float for easy reordering
  content JSONB NOT NULL,
  -- START OF SUB-NOTE FRONTMATTER MODIFICATIONS
  -- Add structured frontmatter fields for sub-notes if needed
  fm_title VARCHAR(255),                      -- Optional title for sub-note
  fm_visibility VARCHAR(50) DEFAULT 'visible', -- Controls visibility in UI (visible, collapsed, hidden)
  fm_style JSONB DEFAULT '{}',                -- Style preferences for this sub-note
  -- END OF SUB-NOTE FRONTMATTER MODIFICATIONS
  is_collapsed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- -- Sub-note history for versioning
-- CREATE TABLE IF NOT EXISTS sub_note_history (
--   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
--   sub_note_id UUID NOT NULL REFERENCES sub_notes(id) ON DELETE CASCADE,
--   content JSONB NOT NULL,
--   modified_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
--   created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
--   CONSTRAINT fk_sub_note FOREIGN KEY (sub_note_id) REFERENCES sub_notes(id) ON DELETE CASCADE
-- );

-- Note links for knowledge graph
CREATE TABLE IF NOT EXISTS note_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  target_note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  source_sub_note_id UUID REFERENCES sub_notes(id) ON DELETE CASCADE,
  link_text VARCHAR(255),
  link_type VARCHAR(50) DEFAULT 'reference', -- 'reference', 'embed', 'transclusion'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(source_note_id, target_note_id, source_sub_note_id, link_text)
);

-- Saved queries
CREATE TABLE IF NOT EXISTS saved_queries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  query_definition JSONB NOT NULL,
  is_public BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Note permissions for shared notes
CREATE TABLE IF NOT EXISTS note_permissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  email VARCHAR(255), -- For sharing by email
  permission_level VARCHAR(20) NOT NULL, -- 'read', 'comment', 'edit', 'admin'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(note_id, user_id),
  UNIQUE(note_id, email),
  CHECK (user_id IS NOT NULL OR email IS NOT NULL)
);

-- User note shortcuts/favorites
CREATE TABLE IF NOT EXISTS user_note_shortcuts (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  PRIMARY KEY (user_id, note_id)
);

-- START OF F   TABLE ADDITION
-- Frontmatter schema definitions table - for defining available frontmatter fields
CREATE TABLE IF NOT EXISTS frontmatter_schemas (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  schema JSONB NOT NULL, -- JSON Schema format to validate frontmatter
  is_system BOOLEAN DEFAULT FALSE, -- Indicates if this is a system-defined schema
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, name)
);

-- Note to frontmatter schema relationship
CREATE TABLE IF NOT EXISTS note_frontmatter_schemas (
  note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  schema_id UUID NOT NULL REFERENCES frontmatter_schemas(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  PRIMARY KEY (note_id, schema_id)
);
-- END OF FRONTMATTER SCHEMA METADATA TABLE ADDITION

-- Full text search vector for notes
ALTER TABLE notes ADD COLUMN search_vector tsvector;
CREATE INDEX IF NOT EXISTS notes_search_idx ON notes USING GIN(search_vector);

-- Full text search vector for sub-notes
ALTER TABLE sub_notes ADD COLUMN search_vector tsvector;
CREATE INDEX IF NOT EXISTS sub_notes_search_idx ON sub_notes USING GIN(search_vector);

-- Note-graph cache for performance
CREATE TABLE IF NOT EXISTS note_graph_cache (
  note_id UUID PRIMARY KEY REFERENCES notes(id) ON DELETE CASCADE,
  connected_notes JSONB NOT NULL DEFAULT '[]', -- Contains array of connected note IDs
  connection_strength INTEGER DEFAULT 0, -- Number of links
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- START OF SEARCH VECTOR UPDATES FOR FRONTMATTER FIELDS
-- Function to update search vector for notes, including frontmatter fields
CREATE OR REPLACE FUNCTION update_note_search_vector() RETURNS trigger AS $$
BEGIN
  NEW.search_vector = 
    setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
    -- Add frontmatter fields to search vector with lower weight
    setweight(to_tsvector('english', COALESCE(NEW.fm_status, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(NEW.fm_author, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(NEW.fm_category, '')), 'C') ||
    setweight(to_tsvector('english', COALESCE(NEW.fm_type, '')), 'C') ||
    -- Also include any text from the metadata JSONB that might be useful for search
    setweight(to_tsvector('english', 
      COALESCE((NEW.metadata->>'title')::text, '') || ' ' || 
      COALESCE((NEW.metadata->>'summary')::text, '') || ' ' ||
      COALESCE((NEW.metadata->>'keywords')::text, '')
    ), 'D');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- END OF SEARCH VECTOR UPDATES FOR FRONTMATTER FIELDS

-- Trigger for updating note search vector
CREATE TRIGGER update_note_search_vector_trigger 
BEFORE INSERT OR UPDATE ON notes
FOR EACH ROW EXECUTE FUNCTION update_note_search_vector();

-- Function to update search vector for sub-notes
CREATE OR REPLACE FUNCTION update_sub_note_search_vector() RETURNS trigger AS $$
BEGIN
  -- Extract text based on content type and update search vector
  IF NEW.type = 'text' OR NEW.type = 'markdown' THEN
    NEW.search_vector = to_tsvector('english', COALESCE(NEW.content->>'text', ''));
  ELSIF NEW.type = 'code' THEN
    NEW.search_vector = to_tsvector('english', 
      COALESCE(NEW.content->>'code', '') || ' ' || 
      COALESCE(NEW.content->>'language', '') || ' ' ||
      COALESCE(NEW.content->>'filename', '')
    );
  ELSE
    -- For other types, index the title/caption if available
    NEW.search_vector = to_tsvector('english', COALESCE(NEW.content->>'caption', ''));
  END IF;
  
  -- Add sub-note frontmatter to search if applicable
  IF NEW.fm_title IS NOT NULL THEN
    NEW.search_vector = NEW.search_vector || to_tsvector('english', NEW.fm_title);
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updating sub-note search vector
CREATE TRIGGER update_sub_note_search_vector_trigger 
BEFORE INSERT OR UPDATE ON sub_notes
FOR EACH ROW EXECUTE FUNCTION update_sub_note_search_vector();

-- Function to update the note graph cache
CREATE OR REPLACE FUNCTION update_note_graph_cache() RETURNS trigger AS $$
DECLARE
  source_connected jsonb;
  target_connected jsonb;
  source_strength int;
  target_strength int;
BEGIN
  -- Get current data or initialize
  SELECT connected_notes, connection_strength 
  INTO source_connected, source_strength
  FROM note_graph_cache 
  WHERE note_id = NEW.source_note_id;
  
  IF NOT FOUND THEN
    source_connected := '[]'::jsonb;
    source_strength := 0;
    INSERT INTO note_graph_cache (note_id, connected_notes, connection_strength, last_updated)
    VALUES (NEW.source_note_id, source_connected, source_strength, NOW());
  END IF;
  
  SELECT connected_notes, connection_strength 
  INTO target_connected, target_strength
  FROM note_graph_cache 
  WHERE note_id = NEW.target_note_id;
  
  IF NOT FOUND THEN
    target_connected := '[]'::jsonb;
    target_strength := 0;
    INSERT INTO note_graph_cache (note_id, connected_notes, connection_strength, last_updated)
    VALUES (NEW.target_note_id, target_connected, target_strength, NOW());
  END IF;
  
  -- Update source note connections
  IF NOT source_connected @> jsonb_build_array(NEW.target_note_id::text) THEN
    source_connected := source_connected || jsonb_build_array(NEW.target_note_id::text);
    source_strength := source_strength + 1;
    
    UPDATE note_graph_cache 
    SET connected_notes = source_connected,
        connection_strength = source_strength,
        last_updated = NOW()
    WHERE note_id = NEW.source_note_id;
  END IF;
  
  -- Update target note connections (backlinks)
  IF NOT target_connected @> jsonb_build_array(NEW.source_note_id::text) THEN
    target_connected := target_connected || jsonb_build_array(NEW.source_note_id::text);
    target_strength := target_strength + 1;
    
    UPDATE note_graph_cache 
    SET connected_notes = target_connected,
        connection_strength = target_strength,
        last_updated = NOW()
    WHERE note_id = NEW.target_note_id;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for updating note graph cache
CREATE TRIGGER update_note_graph_cache_trigger
AFTER INSERT ON note_links
FOR EACH ROW EXECUTE FUNCTION update_note_graph_cache();

-- Clean up graph cache when links are deleted
CREATE OR REPLACE FUNCTION cleanup_note_graph_cache() RETURNS trigger AS $$
DECLARE
  source_connected jsonb;
  target_connected jsonb;
  source_strength int;
  target_strength int;
BEGIN
  -- Get current data
  SELECT connected_notes, connection_strength 
  INTO source_connected, source_strength
  FROM note_graph_cache 
  WHERE note_id = OLD.source_note_id;
  
  SELECT connected_notes, connection_strength 
  INTO target_connected, target_strength
  FROM note_graph_cache 
  WHERE note_id = OLD.target_note_id;
  
  -- Update source note connections
  source_connected := source_connected - OLD.target_note_id::text;
  source_strength := source_strength - 1;
  
  UPDATE note_graph_cache 
  SET connected_notes = source_connected,
      connection_strength = source_strength,
      last_updated = NOW()
  WHERE note_id = OLD.source_note_id;
  
  -- Update target note connections (backlinks)
  target_connected := target_connected - OLD.source_note_id::text;
  target_strength := target_strength - 1;
  
  UPDATE note_graph_cache 
  SET connected_notes = target_connected,
      connection_strength = target_strength,
      last_updated = NOW()
  WHERE note_id = OLD.target_note_id;
  
  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Trigger for cleaning up note graph cache
CREATE TRIGGER cleanup_note_graph_cache_trigger
AFTER DELETE ON note_links
FOR EACH ROW EXECUTE FUNCTION cleanup_note_graph_cache();

-- Function to automatically update timestamps
CREATE OR REPLACE FUNCTION update_timestamp() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create update timestamp triggers for all tables
CREATE TRIGGER update_users_timestamp BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_folders_timestamp BEFORE UPDATE ON folders FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_notes_timestamp BEFORE UPDATE ON notes FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_sub_notes_timestamp BEFORE UPDATE ON sub_notes FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_saved_queries_timestamp BEFORE UPDATE ON saved_queries FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_note_permissions_timestamp BEFORE UPDATE ON note_permissions FOR EACH ROW EXECUTE FUNCTION update_timestamp();
-- START OF FRONTMATTER SCHEMA TIMESTAMP TRIGGERS
CREATE TRIGGER update_frontmatter_schemas_timestamp BEFORE UPDATE ON frontmatter_schemas FOR EACH ROW EXECUTE FUNCTION update_timestamp();
-- END OF FRONTMATTER SCHEMA TIMESTAMP TRIGGERS

-- Update parent note timestamp when sub-note is updated
CREATE OR REPLACE FUNCTION update_parent_note_timestamp() RETURNS trigger AS $$
BEGIN
  UPDATE notes SET updated_at = NOW() WHERE id = NEW.note_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_parent_note_timestamp_trigger
AFTER INSERT OR UPDATE ON sub_notes
FOR EACH ROW EXECUTE FUNCTION update_parent_note_timestamp();

-- Backlinks view for easy querying
CREATE OR REPLACE VIEW note_backlinks AS
SELECT 
  target_note_id AS note_id,
  source_note_id AS referenced_by_note_id,
  source_sub_note_id,
  link_text,
  link_type,
  n.title AS source_note_title,
  n.slug AS source_note_slug
FROM note_links nl
JOIN notes n ON nl.source_note_id = n.id;

-- Function to extract and process note links from markdown content
CREATE OR REPLACE FUNCTION process_markdown_links() RETURNS trigger AS $$
DECLARE
  link_matches TEXT;
  link_pattern TEXT := '\[\[(.*?)(?:\|(.*?))?\]\]';
  link_text TEXT;
  link_target TEXT;
  target_note_id UUID;
  matches TEXT[];
BEGIN
  -- Only process text/markdown content
  IF NEW.type = 'text' OR NEW.type = 'markdown' THEN
    -- Get content text
    link_matches := NEW.content->>'text';
    
    -- Extract all matches
    FOR matches IN SELECT regexp_matches(link_matches, link_pattern, 'g') LOOP
      -- First captured group is the note slug
      link_target := matches[1];
      -- Second captured group is the optional display text
      link_text := COALESCE(matches[2], matches[1]);
      
      -- Find the target note
      SELECT id INTO target_note_id
      FROM notes
      WHERE slug = link_target AND user_id = (
        SELECT user_id FROM notes WHERE id = NEW.note_id
      );
      
      -- If target note exists, create the link
      IF target_note_id IS NOT NULL THEN
        INSERT INTO note_links (
          source_note_id, 
          target_note_id, 
          source_sub_note_id,
          link_text,
          link_type
        ) VALUES (
          NEW.note_id,
          target_note_id,
          NEW.id,
          link_text,
          'reference'
        ) ON CONFLICT (source_note_id, target_note_id, source_sub_note_id, link_text) DO NOTHING;
      END IF;
    END LOOP;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to process markdown links
CREATE TRIGGER process_markdown_links_trigger
AFTER INSERT OR UPDATE ON sub_notes
FOR EACH ROW EXECUTE FUNCTION process_markdown_links();

-- START OF FRONTMATTER PROCESSING FUNCTION
-- Function to extract and store frontmatter from markdown content
CREATE OR REPLACE FUNCTION extract_frontmatter() RETURNS trigger AS $$
DECLARE
  content_text TEXT;
  frontmatter_match TEXT;
  frontmatter_yaml TEXT;
  frontmatter_json JSONB;
  fm_pattern TEXT := '^\s*---\s*\n([\s\S]*?)\n\s*---\s*\n'; -- Matches YAML frontmatter between --- markers
BEGIN
  -- Only process markdown content
  IF NEW.type = 'markdown' THEN
    -- Get content text
    content_text := NEW.content->>'text';
    
    -- Check if there's frontmatter
    IF content_text ~ fm_pattern THEN
      -- Extract frontmatter YAML
      SELECT (regexp_matches(content_text, fm_pattern))[1] INTO frontmatter_yaml;
      
      -- Convert YAML to JSON (simplified approach - for production consider a proper YAML parser)
      -- This is a basic implementation and should be replaced with a proper YAML parser
      BEGIN
        -- Convert YAML key-value pairs to JSON format
        -- This is very simplified and only handles basic YAML
        frontmatter_json := ('{'
          || regexp_replace(
               regexp_replace(
                 regexp_replace(frontmatter_yaml, 
                   '(\w+):\s*(.*)', '"\1": "\2"', 'g'),
                 ',\s*$', '', 'g'),
               '\n', ',', 'g')
          || '}')::JSONB;
          
        -- Get the note
        UPDATE notes 
        SET 
          -- Update common structured fields if they exist in frontmatter
          fm_status = NULLIF(frontmatter_json->>'status', ''),
          fm_priority = (frontmatter_json->>'priority')::INTEGER,
          fm_due_date = NULLIF(frontmatter_json->>'due_date', '')::DATE,
          fm_author = NULLIF(frontmatter_json->>'author', ''),
          fm_category = NULLIF(frontmatter_json->>'category', ''),
          fm_template = NULLIF(frontmatter_json->>'template', ''),
          fm_type = NULLIF(frontmatter_json->>'type', ''),
          fm_last_reviewed_at = NULLIF(frontmatter_json->>'last_reviewed_at', '')::TIMESTAMP WITH TIME ZONE,
          -- Store the full frontmatter in the metadata JSONB
          metadata = metadata || jsonb_build_object('frontmatter', frontmatter_json)
        WHERE id = NEW.note_id;
        
        -- Strip frontmatter from content (optional, depends on if you want to display it)
        -- This keeps the original content with frontmatter
        -- NEW.content = jsonb_set(NEW.content, '{text}', to_jsonb(regexp_replace(content_text, fm_pattern, '')));
      EXCEPTION WHEN OTHERS THEN
        -- If there's an error parsing YAML, just store it as raw text
        UPDATE notes 
        SET metadata = metadata || jsonb_build_object('frontmatter_raw', frontmatter_yaml)
        WHERE id = NEW.note_id;
      END;
    END IF;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to extract frontmatter
CREATE TRIGGER extract_frontmatter_trigger
AFTER INSERT OR UPDATE ON sub_notes
FOR EACH ROW EXECUTE FUNCTION extract_frontmatter();
-- END OF FRONTMATTER PROCESSING FUNCTION

-- Create basic indexes for performance
CREATE INDEX IF NOT EXISTS idx_folders_user_id ON folders(user_id);
CREATE INDEX IF NOT EXISTS idx_folders_parent_id ON folders(parent_id);
CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes(user_id);
CREATE INDEX IF NOT EXISTS idx_notes_folder_id ON notes(folder_id);
CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes(updated_at);
CREATE INDEX IF NOT EXISTS idx_sub_notes_note_id ON sub_notes(note_id);
CREATE INDEX IF NOT EXISTS idx_sub_notes_position ON sub_notes(position);
CREATE INDEX IF NOT EXISTS idx_sub_note_history_sub_note_id ON sub_note_history(sub_note_id);
CREATE INDEX IF NOT EXISTS idx_note_links_source ON note_links(source_note_id);
CREATE INDEX IF NOT EXISTS idx_note_links_target ON note_links(target_note_id);
CREATE INDEX IF NOT EXISTS idx_note_tags_note_id ON note_tags(note_id);
CREATE INDEX IF NOT EXISTS idx_note_tags_tag_id ON note_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_saved_queries_user_id ON saved_queries(user_id);
CREATE INDEX IF NOT EXISTS idx_note_permissions_note_id ON note_permissions(note_id);
CREATE INDEX IF NOT EXISTS idx_note_permissions_user_id ON note_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_note_permissions_email ON note_permissions(email);

-- START OF FRONTMATTER FIELD INDEXES
-- CREATE INDEX IF NOT EXISTSes for common frontmatter fields that will be queried often
CREATE INDEX IF NOT EXISTS idx_notes_fm_status ON notes(fm_status);
CREATE INDEX IF NOT EXISTS idx_notes_fm_priority ON notes(fm_priority);
CREATE INDEX IF NOT EXISTS idx_notes_fm_due_date ON notes(fm_due_date);
CREATE INDEX IF NOT EXISTS idx_notes_fm_author ON notes(fm_author);
CREATE INDEX IF NOT EXISTS idx_notes_fm_category ON notes(fm_category);
CREATE INDEX IF NOT EXISTS idx_notes_fm_type ON notes(fm_type);
CREATE INDEX IF NOT EXISTS idx_notes_fm_last_reviewed_at ON notes(fm_last_reviewed_at);

-- Create indexes for sub-note frontmatter fields
CREATE INDEX IF NOT EXISTS idx_sub_notes_fm_title ON sub_notes(fm_title);
CREATE INDEX IF NOT EXISTS idx_sub_notes_fm_visibility ON sub_notes(fm_visibility);

-- Create indexes for frontmatter schema tables
CREATE INDEX IF NOT EXISTS idx_frontmatter_schemas_user_id ON frontmatter_schemas(user_id);
CREATE INDEX IF NOT EXISTS idx_note_frontmatter_schemas_note_id ON note_frontmatter_schemas(note_id);
CREATE INDEX IF NOT EXISTS idx_note_frontmatter_schemas_schema_id ON note_frontmatter_schemas(schema_id);
-- END OF FRONTMATTER FIELD INDEXES

-- Create GIN index for metadata JSONB
CREATE INDEX IF NOT EXISTS idx_notes_metadata ON notes USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_sub_notes_content ON sub_notes USING GIN(content);
CREATE INDEX IF NOT EXISTS idx_users_preferences ON users USING GIN(preferences);
-- START OF SUB-NOTE FRONTMATTER STYLE INDEX
CREATE INDEX IF NOT EXISTS idx_sub_notes_fm_style ON sub_notes USING GIN(fm_style);
-- END OF SUB-NOTE FRONTMATTER STYLE INDEX

-- Create index for case-insensitive searches
CREATE INDEX IF NOT EXISTS idx_notes_title_lower ON notes(LOWER(title));
CREATE INDEX IF NOT EXISTS idx_tags_name_lower ON tags(LOWER(name));

-- Grant permissions (modify as needed based on your application users)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
