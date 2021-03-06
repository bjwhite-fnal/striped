Striped Concepts and Data Representation
----------------------------------------

Striped Analysis Framework (SAyFork or Striped) is based on the idea of storing the data in a non-relational key/value database in a way suitable for most efficient data
retrieval for analysis purpose. Striped data representation is a kind a columnar data representation. It is designed to represent an list of objects of similar structure or a *dataset*. In High Energy Physics, an object maps to the HEP event. When the data is stored into the Striped database, the dataset is broken into a number of subsets of more or
less equal size. These subsets are called *object groups* or *event groups* in case of HEP. 
Object group size is chosen based on the data characteristics and the efficiency of data storage and analysis. Typically, it is between 10 and 100 thousand objects.

Each member of the object structure for the dataset is stored separately as a possibly multidimensional array of values with first
dimension running along the list of objects and their sub-objects, or a *column*. Columns are broken into segments at the object group boundaries.
The segment of a column is called *stripe* (Hence the name of the Framework) and it is an atomic unit of the data representation in the Striped database.

Data analysis is performed by a set of concurrent workers running the same analysis code, each working on its own set object groups and corresponding stripes.
The framework retrieves the set of stripes for each object group, one after the other, and passes them to the user analysis module running by the worker.

User Analysis Code
------------------

User analysis code consists of 2 parts - *Job* and *Worker*. Roughly, these two parts perform the same functions as the "map" and "reduce" portions of the popular
map/reduce data analysis architecture. The Job runs in the user environment. It defines the dataset, initiates the analysis by communicating to *job_server*,
receives, compiles and represents data received from the Worker. Worker part runs in multiple instances in the worker environment. Each worker runs over its own portion
of the dataset and sends data to the Job.

Worker
~~~~~~

The user analysis code executed by the workers is specified as a Python class with 2 required members:

  * Columns - class member - list of column names used for the analysis
  * run - method - a function which will be called by the worker for each object group

The run method must have 2 arguments in addition to "self":

.. code-block:: python

    class Worker:
    
        Columns = [...]
        
        def run(self, objects, job):
            # ...

"objects" argument passed to the run() method gives the code access to the input data and the "job" argument is used to send output back to the Job.

Object Group Accessor
.....................

First argument of the run() method (objects) is an Object Group Accessor object with the following attributes and methods:

**branch(barnch_name)** - method returning *Branch accessor* for the object group. Calling branch() method is equivalent to accessing the branch as if it was a property of the "objects" object:

.. code-block:: python

    def run(self, objects, job):
        # ... the following are equivalent:
        b1 = objects.branch("Muon")
        b2 = objects.Muon
        
**attr(attribute_name)** - method, returns numpy array with the attribute for all the objects in the object group. Calling attr() method is equivalent to accessing the attribute as if it was a property of the "objects" object:

.. code-block:: python

    class Worker:
    
        Columns = ["event_id"]

        def run(self, objects, job):
            # ... the following are equivalent:
            e1 = objects.attr("event_id")
            e2 = objects.event_id
        
**count** - attribute - returns the number of objects in the group. You can also use len(objects).

**rgid** - attribute - returns the ID of the object group.

**filter(mask)** - method - returns an object filter object. The mask must be a single-dimension boolean (or another type convertible to boolean) numpy array with the size equal
to the number of objects. For example:

.. code-block:: python

    class Worker:
    
        Columns = ["mass"]

        def run(self, objects, job):
            object_filter = objects.filter(object.mass > 4.5)

See *Filters* section below for details.

You can iterate over the Object Group Accessor object, as if it was a list of individual objects. For example:

.. code-block:: python

    class Worker:
    
        Columns = ["mass"]

        def run(self, objects, job):
            for obj in objects:
                mass = obj.mass
                #...

Alternatively, individual objects can be accessed by indexing the Object Group Accessor:

.. code-block:: python

    class Worker:
    
        Columns = ["mass"]

        def run(self, objects, job):
            for i in xrange(objects.count):
                mass = objects[i].mass
                #...


Branch Accessor
...............

Calling **branch** method of the Object Group accessor object returns a Branch Accessor object. This object provides access to members of the individual branch:

**attr(attribute_name)** - method - returns numpy array with the given branch property for all the objects in the object group. Calling attr() method is equivalent to accessing the attribute as if it was a property of the branch accessor object:

.. code-block:: python

    class Worker:
    
        Columns = ["Muon.pt"]

        def run(self, objects, job):
            muons = objects.Muon                    # muons is a Branch Accessor object
            # ... the following are equivalent:
            mu_pt = muons.pt
            mu_pt = muons.attr("pt")

**count** - property - returns the number of branch elements per object in the object group as an integer one-dimensional numpy array

**filter(mask)** - method - returns branch filter object. The mask argument must be a single-dimension boolean (or another type convertible to boolean) numpy array with the size equal to the total number of the branch elements in the object group. For example:

.. code-block:: python

    class Worker:
    
        Columns = ["Muon.pt"]

        def run(self, events, job):
            muon_filter = events.Muon.filter(events.Muon.pt > 300.0)
            # or...
            muons = events.Muon     # muons branch
            muon_filter = muons.filter(muons.pt > 300.0)

See *Filters* section below for details.

**pairs()** - method - creates an accessor for all combinations of branch element pairs. It is called **Combo Accessor**. 
The branch element pairs are constructed from elements of the same event only. If the event 
has 0 or 1 elements of the branch, no pairs are generated by this event. The list of generated pairs does not include swapped pairs. For example, if the event
has 3 elements of the branch, 1,2 and 3, then only 3 pairs will be generated: (1,2), (1,3) and (2,3). The list will *not* include pairs (2,1), (3,1) and (3,2).
Combo Accessor is similar to the Branch Accessor, but there are some differences. Please see below.

You can iterate over the branch accessor object, as if it was a list of individual branch elements:

.. code-block:: python

    class Worker:
    
        Columns = ["Muon.pt"]

        def run(self, events, job):
            muons = events.Muon             # branch accessor
            for mu in muons:
                mu_pt = mu.pt               # "pt" value for individual muon in the entire event group


Object Accessor
...............

When iterating over the Object Group Accessor or applying a numeric index to it, you get an Object Accessor object:

.. code-block:: python

    class Worker:
    
        Columns = ["mass"]

        def run(self, objects, job):
            for obj in objects:                 # obj is an Object Accessor
                #...


Object Accessor is used to access object attributed and branch elements associated with the object. It has the following methods and attributes:

**attr(attribute_name)** - method, returns the value of the object attribute. Calling attr() method is equivalent to accessing the attribute as if it was a property of the Object Accessor:

.. code-block:: python

    class Worker:
    
        Columns = ["mass"]

        def run(self, objects, job):
            for obj in objects:                 # obj is an Object Accessor
                m1 = obj.attr("mass")           # m1 and m2 are the same
                m2 = obj.mass
                

Combo Accessor
..............

**Branch Accessor's** pairs() method returns **Combo Accessor** object. It represents all unique pairs of branch elements for all objects in the group. 
For example, let's say the group consists of 4 "objects" and each object has the folowing number of branch called "observation":

    ======== ========================
    Object    Observations
    ======== ========================
    0          2: o00, o01
    1          4: o10, o11, o12, o13
    2          1: o20
    3          3: o30, o31, o32
    ======== ========================

Then the Object Group's pairs() method will return the Combo Accessor with the following observation pairs:

    ======== ========
    Pair     Object
    ======== ========
    o00 o01   0
    o10 o11   1
    o10 o12   1
    o10 o13   1
    o11 o12   1
    o11 o13   1
    o12 o13   1
    o30 o31   3
    o30 o32   3
    o31 o32   3
    ======== ========

As you can see, the Combo Accessor includes all the pairs generated from the branch elements of the same object. The Combo Accessor can be used to iterate over 
all branch element pairs regardless of which object they belong to. For example:

.. code-block:: python

    class Worker:
    
        Columns = ["muon.p4"]

        def run(self, events, job):
            mu_pairs = events.muon.pairs()                      # this is Combo Accessor object
            for mu_pair in mu_pairs:                            # iteration produces pairs of muons for all the events in the group
                mu1, mu2 = mu_pair                              # unpack the pair
                mu_mu_mass = invariant_mass(mu1.p4, mu2.p4)     # get 4-momentums and calculate the invariant mass
                
                
You can extract first or second member of all pairs from the Combo Accessor:

.. code-block:: python

    class Worker:
    
        Columns = ["muon.p4"]

        def run(self, events, job):
            mu_pairs = events.muon.pairs()                      # this is Combo Accessor object
            mu1, mu2 = mu_pairs                                 # first and second items of each pair
            mu_mu_mass = invariant_mass_array(mu1.p4, mu2.p4)      # calculate invariant masses from vectors
            job.fill(mu_mu_mass = mu_mu_mass)
    
                

Filters
.......

The user can filter objects and branch elements based on some boolean criteria. Filters can be applied to Object Group Accessors, Branch Accessors and
Combo Accessors. When applying a filter to these objects, the result will be the same kind of object but with reduced number of data items in it. 
There are 2 types filters - Object filters and Branch filters. Object filters are created by calling the Object Group Accessor's filter() method and
can be applied to an Object Group Accessor object. Branch filters are created by Branch Accessors and Combo Accessors and can be applied only to the
same accessor object. Filters are created by passing a boolean mask array of corresponding size to the filter() method of the accessor.


.. code-block:: python

    class Worker:
    
        Columns = ["mass","quality"]

        def run(self, objects, job):
            
            fq = objects.filter(objects.quality > 3.5)      # "object.quality > 3.5" is an expression resulting in a boolean numpy array
            good_objects = fq(objects)                      # create new Object Group Accessor with fewer objects
            
            fm = objects.filter(objects.mass > 10.3)        # another filter with another criterion
            heavy_objects = fm(objects)                     # another Object Group Accessor
            
            f_combined = fm * fq                            # filters created by the same original accessor can be combined
            f_combined = fm and fq                          # '*' and 'and' are synonyms, so are '+' and 'or'
            
            f_either_way = fm or fq                         # or'ing the filters
            heavy_or_good = f_either_way(objects)           # apply or'ed filter to the original object group

            job.fill(mass_heavy = heavy_objects.mass)       # accessing "mass" attribute of filtered objects
            job.fill(mass_good = good_objects.mass)

            
            # the following are errors:
            f_combined(heavy_or_good)                       # filter can be applied to its origin only
            fxyz = fm * f_either_way                        # combining filters from different origins


Branch filter examples:

.. code-block:: python

    class Worker:
    
        Columns = ["muon.pt", "muon.eta"]

        def run(self, objects, job):
        
            muons = objects.muon
            high_pt_filter = muon.filter(muon.pt > 100.0)
            
            # filters can be applied to both branches and arrays, so the following 2 lines produce same results:
            
            job.fill(eta=high_pt_filter(muons).eta)         # filter muons, get eta's and store in histogram
            job.fill(eta=high_pt_filter(muons.eta))         # get array with muon eta's, apply filter it and stote in histogram

Object filters can be converted to branch filters. This is done by replicating the object filter mask in such a way that all the branch elements of accepted
objects will be accepted, and vise versa, all the branch elements from the rejected objects will be rejected. Conversion can be done either explicitly, by
passing an existing filter to the filter() method of an accessor, or implicitly when combining filters of 2 different kinds:

.. code-block:: python

    # explicit conversion
    
    class Worker:
    
        Columns = ["mass","component.size","component.price"]

        def run(self, objects, job):
            
            heavy_object_filter = objects.filter(objects.mass > 10.3)
            converted_filter = objects.component.filter(heavy_object_filter)    # explicit conversion, object filter to branch filter
            
            job.fill(heavy_size = converted_filter(objects.component.size))     # histogram sizes of all heavy objects
            
            # implicit conversion: combined filter is a branch filter created from object filter
            # it will accept all the components with size > 3 of all the objects with mass > 10.3
            combined_filter = heavy_object_filter * objects.component.filter(objects.component.size > 3)    
            job.fill(prices_of_bulk_components_of_heavy_objcets = combined_filter(objects.component.price))
            
            
You can use filters with Combo Accessors too. Filters created by Combo Accessors are considered to be Branch Filters.

.. code-block:: python

    class Worker:
    
        Columns = ["muon.p4"]

        def run(self, events, job):
            mu_pairs = events.muon.pairs()                      # this is Combo Accessor object
            mu1, mu2 = mu_pairs                                 # first and second items of each pair
            
            good_pair_filter = mu_pairs.filter((mu1.pt > 100.0) * (mu2.pt > 100.0))
            good_pairs = good_pair_filter(mu_pairs)
            
            mu_mu_mass = invariant_mass_array(good_pairs[0].p4, good_pairs[1].p4)      
            job.fill(mu_mu_mass = mu_mu_mass)
    
                
                

                

                
    








