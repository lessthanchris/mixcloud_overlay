$.ajax({
  url: '/api/get_song',
  success: function( result ) {
    $( "#song_info" ).html(result);
  }
});
