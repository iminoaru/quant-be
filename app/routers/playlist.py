import uuid
from fastapi import APIRouter, HTTPException, Request, Body
from QuantLab_Backend.supabase_client import supabase
from QuantLab_Backend.app.middleware import auth_required
from pydantic import BaseModel
import logging
router = APIRouter()


@router.get("/")
async def get_all_playlists(request: Request):
    
    res = supabase.table("playlists").select("*").execute()
    return res.data


@router.get("/{playlist_id}")
async def get_playlist_by_id(request: Request, playlist_id: str):
    res = supabase.table("playlists").select("*").eq("playlist_id", playlist_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Playlist not found")
    print(res.data[0])
    return res.data[0]


@router.delete("/delete/{playlist_id}")
@auth_required
async def delete_playlist(request: Request, playlist_id: str,):
    playlist = supabase.table("playlists").select("*").eq("playlist_id", playlist_id).execute()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    
    res = supabase.table("playlists").delete().eq("playlist_id", playlist_id).execute()
    return {"message": "Playlist deleted successfully"}


#FIX THIS
@router.get("/users-playlists/{user_id}")
@auth_required
async def get_users_playlists(request: Request, user_id: str):
    
    res = supabase.table("playlists").select("playlist_id", "name", "description", "total_problems", "user_id").eq("user_id", user_id).execute()
  
    print(res.data)
    return res.data


@router.get("/global-playlists")
async def get_global_playlists(request: Request):
    
    res = supabase.table("playlists").select("playlist_id", "name", "description", "total_problems", "user_id").eq("user_id", uuid.UUID('96dd7fd30d4048b8a79e6df9346dabc9').hex).execute()
  
    print(res.data)
    return res.data


class PlaylistCreate(BaseModel):
    user_id: str
    name: str
    description: str = None
    
@router.post("/create")
@auth_required
async def create_playlist(request: Request, playlist: PlaylistCreate = Body(...)):
    try:
        res = (supabase.table("playlists")
        .insert([{"user_id": playlist.user_id, "name": playlist.name, "description": playlist.description}])
        .execute())
        
        res2 = supabase.table("userplaylists").insert([{"user_id": playlist.user_id, "playlist_id": res.data[0]["playlist_id"]}]).execute()
        return {"playlist": res.data, "userplaylist": res2.data}
    except Exception as e:
        logging.error(f"Error creating playlist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/update-details/{playlist_id}")
@auth_required
async def update_playlist_details(request: Request, playlist_id: str, playlist: PlaylistCreate = Body(...)):
    res = supabase.table("playlists").update({"name": playlist.name, "description": playlist.description}).eq("playlist_id", playlist_id).execute()
    return res.data



class Problem(BaseModel):
    playlist_id: str
    problem_id: str

@router.post("/add-problem")
@auth_required
async def add_problem_to_playlist(request: Request, problem: Problem = Body(...)):
    
    # Check if problem is already in playlist
    isAlreadyInPlaylist = supabase.table("playlistproblems").select("*").eq("playlist_id", problem.playlist_id).eq("problem_id", problem.problem_id).execute()
    if len(isAlreadyInPlaylist.data) > 0:
        return {"message": "Problem already in playlist" , "status": "duplicate" }
    
    # Add problem to playlist
    res = (supabase.table("playlistproblems")
    .insert([{"playlist_id": problem.playlist_id, "problem_id": problem.problem_id}])
    .execute())
    
    # Get current total_problems count
    current_playlist = supabase.table("playlists").select("total_problems").eq("playlist_id", problem.playlist_id).execute()
    current_count = current_playlist.data[0]['total_problems'] if current_playlist.data else 0
    
    # Update the total_problems count
    update_res = supabase.table("playlists").update({"total_problems": current_count + 1}).eq("playlist_id", problem.playlist_id).execute()
    
    return {"playlistproblem": res.data, "playlist_update": update_res.data, "status": "success"}

@router.get("/get-problems/{playlist_id}")
async def get_problems_in_playlist(request: Request, playlist_id: str):
    res = (supabase.table("playlistproblems")
    .select("problems!inner(problem_id, name, difficulty, category, company, hints, is_paid, unique_name)")
    .eq("playlist_id", playlist_id)
    .execute())
    
    print(res.data)
    return res.data


@router.delete("/{playlist_id}/problems/{problem_id}")
@auth_required
async def remove_problem_from_playlist(request: Request, playlist_id: str, problem_id: str):
    res = supabase.table("playlistproblems").delete().eq("playlist_id", playlist_id).eq("problem_id", problem_id).execute()
    
    # Get current total_problems count
    current_playlist = supabase.table("playlists").select("total_problems").eq("playlist_id", playlist_id).execute()
    current_count = current_playlist.data[0]['total_problems'] if current_playlist.data else 0
    
    # Update the total_problems count
    update_res = supabase.table("playlists").update({"total_problems": current_count - 1}).eq("playlist_id", playlist_id).execute()
    
    return res.data


