Database
==============

.. code-block:: sql

   update analysestable
   set aliquot_pychron = CAST(analysestable.aliquot as SIGNED INTEGER)
   where `IrradPosition` in #(LIST OF LABNUMBERS)

.. code-block:: sql

   delimiter $$
   CREATE TRIGGER update_aliquot_pychron
   BEFORE INSERT ON analysestable
   FOR EACH ROW BEGIN
   SET NEW.aliquot_pychron = CAST(NEW.aliquot as SIGNED INTEGER);
   END$$
   delimiter ;