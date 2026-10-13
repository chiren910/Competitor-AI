import json


def _get_supabase():
    """Lazily import and return the shared Supabase client."""
    from utils.supabase_client import supabase  # sync client
    return supabase

def safe_parse_json(data):
    """Parse JSON string if needed; return original if parsing fails or data is None."""
    if data is None:
        return None
    if isinstance(data, str):
        try:
            return json.loads(data)
        except Exception:
            return data
    return data


def clean_jsonb_field(value):
    """
    Prepare field value before saving to JSONB column:
    - If empty list, empty string, or None → convert to None (NULL in DB)
    - Else parse JSON safely (if string)
    """
    if value in (None, [], ""):
        return None
    return safe_parse_json(value)


def prepare_data_for_jsonb(data: dict) -> dict:
    """
    Deep clean all values in a dictionary, handling nested structures
    by converting empty lists, empty strings, or None values to None,
    and ensuring all JSON strings are properly parsed.
    """
    if not data:
        return None
        
    result = {}
    for key, value in data.items():
        # Handle nested dictionaries
        if isinstance(value, dict):
            result[key] = prepare_data_for_jsonb(value)
        # Handle lists (potentially of dictionaries)
        elif isinstance(value, list):
            if not value:  # Empty list
                result[key] = None
            else:
                # Process each item in the list
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned_list.append(prepare_data_for_jsonb(item))
                    else:
                        cleaned_list.append(clean_jsonb_field(item))
                result[key] = cleaned_list if cleaned_list else None
        # Handle simple values
        else:
            result[key] = clean_jsonb_field(value)
    
    return result


def check_analysis_exists_sync(link: str, user_id: str) -> bool:
    """
    Check if a competitor analysis already exists for a specific user and link combination.
    Returns True if analysis exists, False otherwise.
    """
    print(f"DEBUG: Checking if analysis exists - link: {link}, user_id: {user_id}")
    
    try:
        resp = _get_supabase().table("competitor_analysis").select("id, created_at").eq("link", link).eq("user_id", user_id).execute()
        
        if hasattr(resp, 'error') and resp.error:
            print(f"ERROR: Database error while checking analysis existence: {resp.error}")
            return False
        
        exists = bool(resp.data and len(resp.data) > 0)
        
        if exists:
            print(f"DEBUG: Analysis EXISTS for user {user_id} and link {link}")
            print(f"DEBUG: Found {len(resp.data)} record(s)")
            # Log creation time for debugging
            if resp.data[0].get('created_at'):
                print(f"DEBUG: Analysis was created at: {resp.data[0]['created_at']}")
        else:
            print(f"DEBUG: Analysis DOES NOT EXIST for user {user_id} and link {link}")
        
        return exists
        
    except Exception as e:
        print(f"ERROR: Exception in check_analysis_exists_sync: {str(e)}")
        return False


def upsert_competitor_analysis_sync(data: dict):
    """
    Upsert competitor_analysis record with enhanced debugging and proper conflict resolution.
    Clean all data to ensure compatibility with JSONB columns.
    Requires 'user_id' and 'link' in data for proper upsert.
    """
    print(f"DEBUG: upsert_competitor_analysis_sync called with data keys: {list(data.keys())}")

    if 'user_id' not in data or 'link' not in data:
        error_msg = "Missing 'user_id' or 'link' in data"
        print(f"ERROR: {error_msg}")
        return {"error": error_msg}

    # Prepare clean data
    clean_data = prepare_data_for_jsonb(data)

    jsonb_fields = [
        "company_profile", "market_data", "market_capture", "local_competitor",
        "national_competitor", "global_competitor", "swot_analysis",
        "comparison_table", "surpass_recommendations"
    ]
    for field in jsonb_fields:
        if field in clean_data:
            clean_data[field] = clean_jsonb_field(clean_data[field])
            if clean_data[field] == []:
                clean_data[field] = None

    try:
        print("DEBUG: Attempting upsert with conflict resolution on user_id, link")
        result = _get_supabase().table("competitor_analysis").upsert(
            clean_data,
            on_conflict="user_id,link"
        ).execute()

        if hasattr(result, 'error') and result.error:
            print(f"ERROR: Supabase returned error: {result.error}")
            return {"error": result.error}
        if not result.data:
            print("ERROR: Supabase returned no data.")
            return {"error": "Supabase returned no data"}

        print("DEBUG: Upsert successful.")
        return result

    except Exception as e:
        print(f"ERROR: Exception during upsert: {str(e)}")
        return {"error": str(e)}


def get_analysis_summary_sync(user_id: str):
    """
    Get a summary of all analyses for a specific user.
    Returns list of analyses with basic info (link, company_name, created_at).
    """
    print(f"DEBUG: Getting analysis summary for user_id: {user_id}")
    
    try:
        resp = _get_supabase().table("competitor_analysis").select(
            "link, company_name, created_at, category"
        ).eq("user_id", user_id).order("created_at", desc=True).execute()
        
        if hasattr(resp, 'error') and resp.error:
            print(f"ERROR: Database error getting analysis summary: {resp.error}")
            return []
        
        analyses = resp.data if resp.data else []
        print(f"DEBUG: Found {len(analyses)} analyses for user {user_id}")
        
        return analyses
        
    except Exception as e:
        print(f"ERROR: Exception in get_analysis_summary_sync: {str(e)}")
        return []


def delete_analysis_sync(link: str, user_id: str):
    """
    Delete a specific analysis for a user and link combination.
    Returns True if successful, False otherwise.
    """
    print(f"DEBUG: Attempting to delete analysis - link: {link}, user_id: {user_id}")
    
    try:
        # First check if the analysis exists
        if not check_analysis_exists_sync(link, user_id):
            print(f"DEBUG: Analysis does not exist, nothing to delete")
            return True  # Consider this a successful operation
        
        # Delete the analysis
        resp = _get_supabase().table("competitor_analysis").delete().eq("link", link).eq("user_id", user_id).execute()
        
        if hasattr(resp, 'error') and resp.error:
            print(f"ERROR: Database error deleting analysis: {resp.error}")
            return False
        
        print(f"DEBUG: Successfully deleted analysis for user {user_id} and link {link}")
        return True
        
    except Exception as e:
        print(f"ERROR: Exception in delete_analysis_sync: {str(e)}")
        return False


def validate_user_and_link_combination(user_id: str, link: str):
    """
    Validate that a user_id and link combination is valid.
    Returns dict with 'valid' boolean and optional 'message'.
    """
    print(f"DEBUG: Validating user_id: {user_id}, link: {link}")
    
    # Basic validation
    if not user_id or not link:
        return {"valid": False, "message": "Both user_id and link are required"}
    
    # Basic URL validation
    if not link.startswith(('http://', 'https://')):
        return {"valid": False, "message": "Link must be a valid URL starting with http:// or https://"}

    # Allow test IDs without DB lookup
    if user_id.lower() in ("test", "test-user", "dev", "demo", "admin"):
        return {"valid": True, "message": "Valid user and link combination"}

    try:
        # Check if user exists in public_users
        user_check = _get_supabase().table("public_users").select("id").eq("id", user_id).execute()
        if not user_check.data:
            return {"valid": False, "message": "Invalid user ID"}
        
        return {"valid": True, "message": "Valid user and link combination"}
        
    except Exception as e:
        print(f"ERROR: Exception in validate_user_and_link_combination: {str(e)}")
        # If Supabase is down/unreachable, don't crash if link is valid
        return {"valid": True, "message": f"Proceeding with caution: {str(e)}"}