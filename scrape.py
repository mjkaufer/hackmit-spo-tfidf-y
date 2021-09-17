# See docs on setup here https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app
# Add client secrets as env vars like so
# export SPOTIPY_CLIENT_ID=...
# export SPOTIPY_CLIENT_SECRET=...
# export SPOTIPY_REDIRECT_URI=...
# for the URI, make sure you add whatever dummy URL you're using to your app
import sys
import spotipy
import spotipy.util as util
import time

class SpotifyScraper:
    def __init__(self, username="mjkaufer"):
        # our spotipy client
        self.sp = None

        self.username = username
        self.lastIndex = {}

    def authenticate(self):
        scope = 'app-remote-control, user-modify-playback-state, streaming, user-read-playback-state, user-read-currently-playing, user-read-private'

        token = util.prompt_for_user_token(self.username, scope)

        if token:
            self.sp = spotipy.Spotify(auth=token)
            print("Successfully authenticated")
        else:
            print("Can't get token for", self.username)

    def getSP(self):
        return self.sp

    def getArtistDiscography(self, artistId="5K4W6rqBFWDnAN6FQUkS6x"):

        artistAlbums = self.sp._get("artists/{}/albums?include_groups=album,single".format(artistId))['items']
        albumTrackDict = {album['id']:None for album in artistAlbums}
        trackToName = {}
        albumToName = {album['id']: album['name'] for album in artistAlbums}

        for albumId in albumTrackDict.keys():
            albumTracks = self.sp._get("albums/{}/tracks?limit=50".format(albumId))['items']

            albumTrackDict[albumId] = {albumTrack['id'] for albumTrack in albumTracks}
            for albumTrack in albumTracks:
                trackToName[albumTrack['id']] = albumTrack['name']



        return albumTrackDict, trackToName, albumToName

    # don't make query num bigger than 50 or it gets angry for some reason
    def playlistQuery(self, queryString, desiredTracks, existingPlaylist={}, queryNum=50):
        if queryString not in self.lastIndex:
            self.lastIndex[queryString] = 0
        playlistQueryResult = self.sp.search(queryString, limit=queryNum, offset=self.lastIndex[queryString], type='playlist')['playlists']['items']

        self.lastIndex[queryString] += queryNum

        results = {playlist['id']:None for playlist in playlistQueryResult}


        for playlistId in results.keys():
            if playlistId in existingPlaylist:
                continue

            playlistTracks = self.sp._get('playlists/{}/tracks?fields=items.track.id'.format(playlistId))['items']
            numTracks = len(playlistTracks)

            relevantTracks = []
            for track in playlistTracks:
                # spotify sometimes has stuff like {track: None}
                if ('track' in track
                    and track['track'] is not None
                    and 'id' in track['track']
                    and track['track']['id'] in desiredTracks):
                    relevantTracks.append(track['track']['id'])

            # only care about playlists that have more than 1 relevant song
            if len(relevantTracks) > 1:
                results[playlistId] = {"tracks": relevantTracks, "total": numTracks}
                print("+", end='')
            else:
                print(".", end='')

            # take a breather!
            time.sleep(0.05)

        return {**{k: v for k, v in results.items() if v is not None}, **existingPlaylist}


if __name__ == '__main__':
    artistId = sys.argv[2] if 2 in sys.argv else '5BvJzeQpmsdsFp4HGUYUEx'
    scraper = SpotifyScraper()
    scraper.authenticate()
    discography, trackToName, albumToName = scraper.getArtistDiscography(artistId=artistId)
    tracks = {song for songs in discography.values() for song in songs}

    print("Discography is", discography)

    runningPlaylistResults = {}
    try:
        for i in range(4):
            for genre in ["indie", "indie rock", "indie pop", "2000s indie", "indie punk"]:
                runningPlaylistResults = scraper.playlistQuery(genre, tracks, runningPlaylistResults)
    except:
        print("Short circuiting, got an error :(")
    finally:
        print("Output is", runningPlaylistResults)

        # print("Sanitized output is", runningPlaylistResults)
        print("Output that looks purdy")

        print({k:{**v, 'tracks': [trackToName[t] for t in v['tracks']]} for k,v in runningPlaylistResults.items()})

    # mapped_discography = {albumToName[k]:[trackToName[el] for el in v] for k,v in discography.items()}
    # print("mapped disco is", mapped_discography)


#     tracks = set("""4S8d14HvHb70ImctNgVzQQ
# 78TTtXnFQPzwqlbtbwqN0y
# 1PS1QMdUqOal0ai3Gt7sDQ
# 2gZUPNdnz5Y45eiGxpHGSc
# 3U21A07gAloCc4P7J8rxcn
# 6C7RJEIUDqKkJRZVWdkfkH
# 4EWCNWgDS8707fNSZ1oaA5
# 722tgOgdIbNe3BEyLnejw4
# 19a3JfW8BQwqHWUMbcqSx8
# 2KpCpk6HjXXLb7nnXoXA5O""".split("\n"))
#     runningPlaylistResults = {}
#     for i in range(3):
#         for genre in ["rap", "hip hop"]:
#             runningPlaylistResults = scraper.playlistQuery(genre, tracks, runningPlaylistResults)

#     print(runningPlaylistResults)
