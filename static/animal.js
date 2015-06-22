
////////////
/* MODELS */
////////////

var Animal = Backbone.Model.extend({
  defaults: {
    name: 'Fido',
    color: 'black',
    sound: 'woof'
  },
  validate: function(attrs, options){
    if (!attrs.name){
        alert('Your animal must have a name!');
    }
    if (attrs.name.length < 2){
        alert('Your animal\'s name must have more than one letter!');
    }
  },
  sleep: function(){
    alert(this.get('name') + ' is sleeping.');
  }
});


///////////
/* VIEWS */
///////////

var AnimalView = Backbone.View.extend({
  tagName: 'li', // defaults to div if not specified
  className: 'animal', // optional, can also set multiple like 'animal dog'
  id: 'dogs', // also optional
  events: {
    'click':         'alertTest',
    'click .edit':   'editAnimal',
    'click .delete': 'deleteAnimal'
  },
  newTemplate: _.template('<%= name %> is <%= color %> and says <%= sound %>'), // inline template
  initialize: function() {
    this.render(); // render is an optional function that defines the logic for rendering a template
  },
  render: function() {
    // the below line represents the code prior to adding the template
    // this.$el.html(this.model.get('name') + ' is ' + this.model.get('color') + ' and says ' + this.model.get('sound'));
    this.$el.html(this.newTemplate(this.model.toJSON())); // calls the template
  }
});



// sets variable source to the animalTemplate id in index.html
var source = document.getElementById("animalTemplate").innerHTML;

// Handlebars compiles the above source into a template
var template = Handlebars.compile(source);

// data
var data = {animals: [
  {type: "Dog", sound: "woof"},
  {type: "Cat", sound: "meow"},
  {type: "Cow", sound: "moo"}
]};

// data is passed to above template
var output = template(data);

// HTML element with id "animalList" is set to the output above
document.getElementById("animalList").innerHTML = output;




