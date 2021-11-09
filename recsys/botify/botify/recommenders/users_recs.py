import random

from .recommender import Recommender


class UsersRecs(Recommender):
    def __init__(self,
                 catalog,
                 users_recs_redis,
                 tracks_redis,
                 artists_redis,
                 user_sess_hits):
        self.catalog = catalog
        self.users_recs_redis = users_recs_redis
        self.user_sess_hits = user_sess_hits
        self.tracks_redis = tracks_redis
        self.artists_redis = artists_redis

    def recommend_next(self, user: int, prev_track: int, prev_track_time: float) -> int:
        recs = self.users_recs_redis.get(user)
        if recs is not None:
            recs = self.catalog.from_bytes(recs)
        else:
            return self.fallback.recommend_next(user, prev_track, prev_track_time)

        self.user_sess_hits.setdefault(user, []).append(prev_track)

        for prev_tracks in self.user_sess_hits[user]:
            if prev_tracks in recs:
                recs.remove(prev_tracks)

        if len(recs) > 1:
            index = random.randint(0, len(recs) - 1)
            return recs[index]
        else:
            # if no recommendations left - use a Sticky Artist recommender
            track_data = self.tracks_redis.get(prev_track)
            if track_data is not None:
                track = self.catalog.from_bytes(track_data)
            else:
                raise ValueError(f"Track not found: {prev_track}")

            artist_data = self.artists_redis.get(track.artist)
            if artist_data is not None:
                artist_tracks = self.catalog.from_bytes(artist_data)
            else:
                raise ValueError(f"Artist not found: {prev_track}")

            index = random.randint(0, len(artist_tracks) - 1)
            return artist_tracks[index]
